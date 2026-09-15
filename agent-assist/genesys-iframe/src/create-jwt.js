const fs = require('fs');
const jwtLib = require('jsonwebtoken');
const path = require('path');

/**
 * If you want to generate your own private/public key pair, you can use commands like the following.
 *
 * ssh-keygen -t rsa -b 4096 -m PEM -f example-jwtRS256.key
 * openssl rsa -in example-jwtRS256.key -pubout -outform PEM -out example-jwtRS256.key.pub
 */

// *** DO NOT USE THE PUBLIC AND PRIVATE KEYS FROM THIS EXAMPLE FOR PRODUCTION USE! ***

/**
 * This is your private key that you will keep on your server. This is used to sign the jwt. You will paste your public
 * key into the appropriate field on the Security tab of the web chat settings page. IBM watsonx Assistant will use your
 * public key to validate the signature on the jwt.
 */
const PRIVATE_KEY = fs.readFileSync(path.join(__dirname, '../keys/example-jwtRS256.key'));

/**
 * Optional: restrict which Genesys environments this server will talk to.
 * Leave empty to allow any pcEnvironment value passed by the client.
 */
const ALLOWED_ENVIRONMENTS = [
    // e.g. 'mypurecloud.com', 'mypurecloud.ie', 'mypurecloud.com.au'
];

/**
 * This is the array of organization ids that the agent is allowed to belong to. At least one value here is required. Without this, this
 * server will generate a jwt for any agent belonging to any Genesys organization.
 */
const ALLOWED_ORG_IDS = [ '5744345c-fb43-4393-b254-704a5cf649b6' ];

// This is the id of the organization 

/**
 * This function handles the http request to create a jwt. I will exchange the Genesys provided oauth code for a jwt signed with the
 * customer's key.
 */
async function handleCreateJwt(request, response) {
    const { code, codeVerifier, redirectUri, clientId, environment } = request.body;

    // ── Validate inputs ───────────────────────────────────────────────────────
    if (!code || !codeVerifier || !redirectUri || !clientId || !environment) {
        response.status(400).json({ error: 'Missing required fields: code, codeVerifier, redirectUri, clientId, environment' });
        return;
    }

    if (ALLOWED_ENVIRONMENTS.length > 0 && !ALLOWED_ENVIRONMENTS.includes(environment)) {
        response.status(400).json({ error: `Environment "${environment}" is not allowed by this server.` });
        return;
    }

    // ── Step 1: Exchange code + verifier for access token.
    const tokenUrl = `https://login.${environment}/oauth/token`;

    let accessToken;
    try {
        const tokenRes = await fetch(tokenUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({
                grant_type:    'authorization_code',
                code,
                redirect_uri:  redirectUri,
                client_id:     clientId,
                code_verifier: codeVerifier,
            }).toString(),
        });

        if (!tokenRes.ok) {
            const text = await tokenRes.text();
            console.error(`[createJwt] Token exchange failed (${tokenRes.status}): ${text}`);
            response.status(502).json({ error: `Genesys token exchange failed: ${tokenRes.status}` });
            return;
        }

        const tokenData = await tokenRes.json();
        if (!tokenData.access_token) {
            console.error('[createJwt] Token response missing access_token:', tokenData);
            response.status(502).json({ error: 'Genesys token response did not include an access_token' });
            return;
        }

        accessToken = tokenData.access_token;
    } catch (err) {
        console.error('[createJwt] Token exchange network error:', err);
        response.status(502).json({ error: 'Network error contacting Genesys token endpoint' });
        return;
    }

    // ── Step 2: Resolve agent identity and org.
    const authHeaders = { Authorization: `Bearer ${accessToken}` };

    let me, org;
    try {
        const [meRes, orgRes] = await Promise.all([
            fetch(`https://api.${environment}/api/v2/users/me`, { headers: authHeaders }),
            fetch(`https://api.${environment}/api/v2/organizations/me`, { headers: authHeaders }),
        ]);

        if (!meRes.ok) {
            const text = await meRes.text();
            console.error(`[createJwt] /users/me failed (${meRes.status}): ${text}`);
            response.status(502).json({ error: `Users call failed` });
            return;
        }
        if (!orgRes.ok) {
            const text = await orgRes.text();
            console.error(`[createJwt] /organizations/me failed (${orgRes.status}): ${text}`);
            response.status(502).json({ error: `Organizations called failed` });
            return;
        }

        [me, org] = await Promise.all([meRes.json(), orgRes.json()]);
    } catch (error) {
        console.error('[createJwt] Genesys API network error:', error);
        response.status(502).json({ error: 'Network error contacting Genesys API' });
        return;
    }

    console.log(`[createJwt] Got users response`, JSON.stringify(me));
    console.log(`[createJwt] Got organizations response`, JSON.stringify(org));

    if (!me.id) {
        console.error('[createJwt] /users/me response missing id:', me);
        response.status(502).json({ error: 'User information not found' });
        return;
    }

    if (!org.id) {
        console.error('[createJwt] /organizations/me response missing id:', me);
        response.status(502).json({ error: 'Organization information not found' });
        return;
    }

    if (!ALLOWED_ORG_IDS.includes(org.id)) {
        console.error('[createJwt] Organization ${org.id} is not authorized', me);
        response.status(403).json({ error: "This user's organization is not authorized" });
        return;
    }

    // Create a customer jwt.
    const jwt = createJwt(me.id);

    // Return the jwt to the client.
    const identity = { user_id: me.id, jwt };

    console.log(`[createJwt] Resolved agent: ${identity.id} (${identity.name}) org: ${identity.organizationId} (${identity.organizationName})`);
    response.json(identity);
}

/**
 * Creates a signed jwt for the agent with the given id.
 */
function createJwt(userId) {
    // This is the content of the JWT. You would normally look up the user information from a user profile.
    const jwtContent = {
        /**
         * This is the subject of the JWT which will be the ID of the user. In a production environment, this code would
         * generally do something such as access a server session object that contains the already-authenticated user
         * information and place the current user's ID here.
         *
         * This user ID will be available under integrations.channel.private.user.id in dialog and
         * system_integrations.channel.private.user.id in actions.
         */
        sub: userId,
    };

    /**
     * Now sign the jwt content to make the actual jwt. We are giving this a very short expiration time (10 seconds)
     * to demonstrate the web chat capability of fetching a new token when it expires. In a production environment,
     * you would likely want to set this to a much higher value or leave it out entirely.
     */
    const jwtString = jwtLib.sign(jwtContent, PRIVATE_KEY, {
        algorithm: 'RS256',
        expiresIn: '1h',
    });

    return jwtString;
}

module.exports = { createJwt, handleCreateJwt };
