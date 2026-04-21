/**
 * JWT Creation Service for watsonx Orchestrate Secure Embed Chat
 *
 * This module handles the server-side creation of JSON Web Tokens (JWTs) for secure
 * authentication with IBM watsonx Orchestrate embed chat.
 *
 * SECURITY MODEL:
 * When security is enabled, all communication relies on:
 * - Authenticated requests via JSON Web Tokens (JWT)
 * - Signed tokens using RS256 algorithm with your private key
 * - Encrypted payloads through RSA public-key cryptography
 * - User identity verification for access control
 *
 * TWO INDEPENDENT RSA KEY PAIRS:
 * 1. Client Application Key Pair (Your Identity):
 *    - Private key: Signs JWTs (kept secure on your server)
 *    - Public key: Uploaded to watsonx Orchestrate for JWT verification
 *    - Purpose: Authenticates your application and verifies token integrity
 *
 * 2. IBM Key Pair (For Encrypted Payloads):
 *    - Public key: Shared with you to encrypt user_payload section
 *    - Private key: Held by IBM to decrypt user_payload
 *    - Purpose: Ensures sensitive user context cannot be inspected by intermediaries
 *    - Note: Only required if using On-Behalf-Of (OBO) flow with sso_token
 *
 * AUTHENTICATION FLOW:
 * 1. Your web application generates a JWT signed with your client private key
 * 2. JWT includes user identity (sub) and optionally encrypted user_payload
 * 3. Every API request to embed chat includes this JWT
 * 4. watsonx Orchestrate validates the JWT signature using your client public key
 * 5. If valid, the request is authenticated and authorized under User permissions
 *
 * VOICE CAPABILITIES:
 * Voice interactions use the same security model:
 * - Voice audio streams are authenticated through JWT tokens
 * - Audio session is tied to the user identity
 * - Same encryption and validation as text-based interactions
 *
 * This module demonstrates:
 * 1. RS256 JWT signing using your private key
 * 2. Optional user payload encryption using IBM's public key
 * 3. Cookie-based user tracking for session continuity
 * 4. Session-based user information enrichment
 *
 * For complete documentation, see:
 * - https://developer.watson-orchestrate.ibm.com/webchat/get_started
 * - https://developer.watson-orchestrate.ibm.com/webchat/context_variables
 * - https://www.ibm.com/docs/en/watsonx/watson-orchestrate/base?topic=applications-securing-embedded-chat
 *
 * CRITICAL SECURITY NOTES:
 * - Never expose your private key to the client side
 * - Always generate JWTs server-side only
 * - Use HTTPS in production environments
 * - Maximum JWT expiry: 7100 seconds (~118 minutes)
 * - Implement token refresh using updateAuthToken() method
 * - Rotate keys regularly according to your security policies
 */

const fs = require("fs");
const path = require("path");
const express = require("express");
const { v4: uuid } = require("uuid");
const jwtLib = require("jsonwebtoken");
const NodeRSA = require("node-rsa");

const router = express.Router();

/**
 * Load your server-side RSA private key (PEM format)
 *
 * This key is used to sign JWTs with the RS256 algorithm. The corresponding public key
 * must be uploaded to your watsonx Orchestrate instance security settings.
 *
 * IMPORTANT: Keep this file secure and never expose it to clients!
 *
 * Generate a new key pair using either method:
 *
 * Method 1 - Using ssh-keygen:
 *   ssh-keygen -t rsa -b 4096 -m PEM -f example-jwtRS256.key
 *   openssl rsa -in example-jwtRS256.key -pubout -outform PEM -out example-jwtRS256.key.pub
 *
 * Method 2 - Using openssl directly:
 *   openssl genrsa -out example-jwtRS256.key 4096
 *   openssl rsa -in example-jwtRS256.key -pubout -out example-jwtRS256.key.pub
 */
const PRIVATE_KEY_PATH = path.join(__dirname, "../keys/example-jwtRS256.key");
if (!fs.existsSync(PRIVATE_KEY_PATH)) {
  throw new Error(`Private key not found at ${PRIVATE_KEY_PATH}`);
}
const PRIVATE_KEY = fs.readFileSync(PRIVATE_KEY_PATH);

/**
 * Load IBM's RSA public key (PEM format)
 *
 * This key is provided by IBM watsonx Orchestrate and is used to encrypt the user_payload
 * field in the JWT. This ensures that sensitive user information cannot be read by clients,
 * as only IBM's servers can decrypt it.
 *
 * You can obtain this key by:
 * 1. Running the wxo-embed-security-v4.sh script (recommended)
 * 2. Calling the generate-key-pair API endpoint manually
 *
 * The encrypted payload will be decrypted server-side by watsonx Orchestrate.
 */
const IBM_PUBLIC_KEY_PATH = path.join(__dirname, "../keys/ibmPublic.key.pub");
if (!fs.existsSync(IBM_PUBLIC_KEY_PATH)) {
  throw new Error(`IBM public key not found at ${IBM_PUBLIC_KEY_PATH}`);
}
const IBM_PUBLIC_KEY = fs.readFileSync(IBM_PUBLIC_KEY_PATH);

/**
 * Cookie lifetime configuration
 *
 * This defines how long the anonymous user ID cookie will persist.
 * Set to a reasonable duration for maintaining user session continuity.
 * Note: This is separate from JWT expiration (max 7100 seconds).
 */
const COOKIE_MAX_AGE = 45 * 24 * 60 * 60 * 1000; // 45 days in milliseconds

/**
 * Create a signed JWT string for the wxO embed chat client
 *
 * This function constructs a JWT with the following structure:
 *
 * @param {string} secureUserID - A stable identifier for users (from cookie)
 * @param {object|null} sessionInfo - Optional authenticated user session data
 *
 * JWT Claims:
 * - sub: Subject (user identifier) - should be a stable, unique ID for the user
 * - user_payload: (Optional) Encrypted user data that will be decrypted by watsonx Orchestrate
 *   - sso_token: Single sign-on token (ONLY supported field in user_payload)
 * - context: Additional context data accessible by the agent
 *   - Custom context variables (e.g., clientID, name, role)
 *   - NOTE: Do NOT use 'wxo_' prefix - it's reserved for system variables
 *
 * For more details on supported fields and context variables, see:
 * https://developer.watson-orchestrate.ibm.com/webchat/context_variables
 *
 * @returns {string} A signed JWT token string
 */
function createJWTString(secureUserID, sessionInfo) {
  // Base JWT claims structure
  // Customize these fields based on your application's requirements
  const jwtContent = {
    // Subject: Unique identifier for the user
    // Using the secure user ID from the cookie
    sub: secureUserID,
    
    // User payload: Will be encrypted with IBM's public key
    // This data is sensitive and will only be readable by watsonx Orchestrate servers
    // IMPORTANT: Only 'sso_token' field is supported in user_payload
    // See: https://developer.watson-orchestrate.ibm.com/webchat/context_variables
    user_payload: {
      sso_token: "sso_token",
    },
    
    // Context: Additional metadata accessible by the agent
    // This data is NOT encrypted and can be read by the client
    // NOTE: Do NOT use 'wxo_' prefix for custom variables - it's reserved for system use
    // See: https://developer.watson-orchestrate.ibm.com/webchat/context_variables
    context: {
      clientID: "865511",      // Your client/organization ID
      name: "Ava",             // Display name in chat
      role: "Admin",           // User role
    },
  };

  // Enrich the JWT with authenticated session data if available
  // In production, this would come from your authentication system
  // IMPORTANT: Only sso_token is supported in user_payload
  if (sessionInfo && sessionInfo.ssoToken) {
    jwtContent.user_payload.sso_token = sessionInfo.ssoToken;
  }

  // Encrypt the user_payload using IBM's RSA public key
  // This ensures sensitive user data cannot be read by clients
  // Only watsonx Orchestrate servers can decrypt this data
  if (jwtContent.user_payload) {
    const rsaKey = new NodeRSA(IBM_PUBLIC_KEY);
    const dataString = JSON.stringify(jwtContent.user_payload);
    const utf8Data = Buffer.from(dataString, "utf-8");
    // Encrypt and encode as base64 string
    jwtContent.user_payload = rsaKey.encrypt(utf8Data, "base64");
  }

  // Sign the JWT using RS256 algorithm with your private key
  // The token expiration should be set based on your security requirements
  // IMPORTANT: Maximum expiry time is 7100 seconds (~118 minutes)
  // Common values: "1h" (3600s), "2h" (7200s - exceeds max, use 7100s instead)
  const jwtString = jwtLib.sign(jwtContent, PRIVATE_KEY, {
    algorithm: "RS256",
    expiresIn: "3600s", // 1 hour - adjust based on your needs (max: 7100s)
  });

  return jwtString;
}

/**
 * Retrieve or create a stable secure user ID stored in a cookie
 *
 * This function ensures that users maintain a consistent identity across
 * page refreshes and sessions. The ID is stored in a secure HTTP-only cookie.
 *
 * Benefits:
 * - Prevents user identity from changing mid-session
 * - Enables conversation continuity for users
 * - Provides basic user tracking without requiring authentication
 *
 * @param {object} request - Express request object
 * @param {object} response - Express response object
 * @returns {string} The secure user ID
 */
function getOrSetSecureUserID(request, response) {
  // Check if a secure user ID already exists in cookies
  let secureUserID = request.cookies["SECURE-USER-ID"];
  
  // Generate a new ID if none exists
  if (!secureUserID) {
    // Create a short, readable ID using UUID (first 5 characters for demo)
    // In production, you might want to use the full UUID for better uniqueness
    secureUserID = `user-${uuid().slice(0, 5)}`;
  }

  // Set/refresh the cookie with each request to maintain the session
  // Note: Cookie expiration is independent of JWT expiration (max 7100s)
  response.cookie("SECURE-USER-ID", secureUserID, {
    maxAge: COOKIE_MAX_AGE,  // Cookie lifetime (45 days)
    httpOnly: true,          // Prevents client-side JavaScript from accessing the cookie (security)
    sameSite: "Lax",         // Provides CSRF protection while allowing normal navigation
    secure: false,           // Set to true in production when using HTTPS
  });

  return secureUserID;
}

/**
 * Parse authenticated session information from cookies
 *
 * This function retrieves user session data if the user is authenticated.
 * In a production application, you would:
 * 1. Verify the session token/cookie
 * 2. Fetch user information from your database or identity provider
 * 3. Validate user permissions
 *
 * For this demo, we simply parse a JSON string from a cookie.
 *
 * @param {object} request - Express request object
 * @returns {object|null} Session info object or null if not authenticated
 */
function getSessionInfo(request) {
  const sessionInfo = request.cookies?.SESSION_INFO;
  if (!sessionInfo) return null;
  
  try {
    // Parse the JSON session data
    return JSON.parse(sessionInfo);
  } catch {
    // Return null if parsing fails (invalid JSON)
    return null;
  }
}

/**
 * Express route handler for JWT creation
 *
 * This endpoint is called by the client to obtain a fresh JWT token.
 * The token is required for secure authentication with watsonx Orchestrate embed chat.
 *
 * Flow:
 * 1. Retrieve or create a secure user ID (stored in cookie)
 * 2. Check for authenticated session information
 * 3. Generate a signed JWT with user data
 * 4. Return the JWT as plain text response
 *
 * The client will include this JWT in the wxOConfiguration.token field
 * when initializing the embed chat.
 *
 * @param {object} request - Express request object
 * @param {object} response - Express response object
 */
function createJWT(request, response) {
  // Ensure we have a stable user ID
  const secureUserID = getOrSetSecureUserID(request, response);
  
  // Get authenticated session data if available
  const sessionInfo = getSessionInfo(request);

  // Create and sign the JWT
  const token = createJWTString(secureUserID, sessionInfo);
  
  // Return the JWT as plain text
  response.send(token);
}

// Define the GET endpoint that returns a signed JWT string
// This endpoint is called by the client before initializing the chat
router.get("/", createJWT);

module.exports = router;
