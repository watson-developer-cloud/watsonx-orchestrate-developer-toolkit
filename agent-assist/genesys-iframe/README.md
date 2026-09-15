# Genesys iframe — watsonx Orchestrate Agent Assist

Reference implementation for the token-exchange server required when embed security is enabled for the watsonx Orchestrate agent assist dashboard in Genesys.

## Usage

1. Place your RSA private key file in the `keys/` directory (the example key is for local development only)
2. Open `src/create-jwt.js` and update:
   - `PRIVATE_KEY` — update the filename to match your key file
   - `ALLOWED_ORG_IDS` — replace with your Genesys organization ID(s)
   - `ALLOWED_ENVIRONMENTS` — optionally restrict which Genesys environments are accepted (e.g. `mypurecloud.com`)
3. Install dependencies: `npm install`
4. Start the server: `node src/server.js` (runs on port 3100)

The server must be reachable over HTTPS at a public URL.
