# Anonymous Embed Chat for IBM watsonx Orchestrate (Sample)

**For complete documentation, please visit:**
- [Getting Started with Embedded Chat](https://developer.watson-orchestrate.ibm.com/webchat/get_started)
- [Context Variables](https://developer.watson-orchestrate.ibm.com/webchat/context_variables)
- [IBM Docs: Securing Embedded Chat](https://www.ibm.com/docs/en/watsonx/watson-orchestrate/base?topic=applications-securing-embedded-chat)

## Overview

This example demonstrates a simple, anonymous embed chat integration **without security enabled**. When security is disabled, anonymous authentication is enabled for a limited set of APIs required for the chat to work for anonymous users.

### ⚠️ Critical Security Warning

**Use this mode ONLY when:**
- You're in development/testing phase
- Your chatbot is public-facing and doesn't require user authentication
- You're building a proof-of-concept
- **Your instance does NOT show or provide access to sensitive data**
- **Your instance does NOT have tools configured with functional credentials that access sensitive data in protected systems**

### 🔒 When to Use Secure Mode Instead

**You MUST use [secure-embed-chat-node](../secure-embed-chat-node) if:**
- You're deploying to production with authenticated users
- Your instance accesses sensitive data or protected systems
- You need user-specific context or audit trails
- You're implementing SSO or On-Behalf-Of (OBO) flow
- Your application requires compliance with security standards

**Before disabling security, you must:**
1. Review ALL integrations in your instance
2. Ensure no sensitive data is exposed
3. Verify no tools have credentials accessing protected systems
4. Document the security decision and rationale

## What This Example Demonstrates

- Basic wxO embed chat integration without JWT authentication
- Simple HTML page with embedded chat
- Anonymous user access (no authentication required)
- Limited API access (only anonymous-enabled endpoints)

## Security Implications

### What You Lose Without Security

When security is disabled, you lose:
- **User authentication** - No way to verify user identity
- **Access control** - Cannot restrict access based on user permissions
- **Encrypted payloads** - Sensitive data cannot be securely transmitted
- **Audit trails** - Limited ability to track user actions
- **SSO integration** - Cannot use On-Behalf-Of (OBO) flow
- **User context** - Cannot pass authenticated user information

### Risks of Anonymous Mode

- **Data exposure** - Any data accessible to the agent is accessible to anyone
- **Unauthorized access** - No way to prevent access to the chat
- **No accountability** - Cannot track who performed what actions
- **Limited functionality** - Some features require authenticated users
- **Compliance issues** - May not meet regulatory requirements

## Running the Code

This example requires having NodeJS installed (version 16.15.1 or higher).

### Running the Server

The server serves the static HTML file from `http://localhost:5555`.

1. Navigate to the anonymous-embed-chat-node directory:
   ```bash
   cd embed_chat_examples/anonymous-embed-chat-node
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the server:
   ```bash
   npm start
   ```
4. The server will be available at `http://localhost:5555`.

### Viewing the Example

- After starting the server, open [http://localhost:5555/](http://localhost:5555/) in your browser.
- The wxO embed chat will load without requiring authentication.

## Setting up your own agent

This example is configured to use placeholder values. To use your own agent:

1. **Configure your agent**:
   - Open [`static/index.html`](static/index.html)
   - Replace the entire `wxOConfiguration` object with the configuration from your embed script
   - You can find the embed script in your agent's settings in the watsonx Orchestrate console
   - The `wxOConfiguration` should include:
     - `orchestrationID` - Your orchestration ID from the embed code
     - `hostURL` - Your watsonx Orchestrate instance URL
     - `agentId` - Your agent's unique identifier
     - `agentEnvironmentId` - Your agent's environment identifier (optional)
   
   **Note about `agentEnvironmentId`:**
   - This field is **optional** and **not required** for draft environments
   - Only include `agentEnvironmentId` when connecting to a **live environment**
   - For draft environments, you can omit this field from the configuration

2. **Disable security in watsonx Orchestrate** (if enabled):
   - Open the Security settings for your wxO embed chat in the watsonx Orchestrate console
   - Ensure security is disabled for anonymous access
   - For detailed instructions, see the [IBM Docs: Securing Embedded Chat](https://www.ibm.com/docs/en/watsonx/watson-orchestrate/base?topic=applications-securing-embedded-chat)

## Key Files

- [`server.js`](server.js) - Simple Express server for serving static files
- [`static/index.html`](static/index.html) - wxO embed chat integration without authentication

## When to Use This Example

Use this anonymous embed chat example **ONLY** when:
- You're in development/testing phase
- Your chatbot is public-facing and doesn't require user authentication
- You're building a proof-of-concept or demo
- **No sensitive data or systems are accessed**
- **No compliance requirements exist**

## When to Use Secure Embed Chat

Switch to the [secure-embed-chat-node](../secure-embed-chat-node) example when:
- You need to authenticate users
- You're deploying to production with authenticated users
- You need to pass user-specific context or data
- You require audit trails of user interactions
- Your instance accesses sensitive data or protected systems
- You need SSO integration or On-Behalf-Of (OBO) flow
- Compliance or regulatory requirements apply

## Comparison: Anonymous vs Secure

| Feature | Anonymous (This Example) | Secure |
|---------|-------------------------|--------|
| User Authentication | ❌ No | ✅ Yes |
| JWT Required | ❌ No | ✅ Yes |
| Encrypted Payloads | ❌ No | ✅ Yes |
| User Context | ❌ None | ✅ Full |
| Audit Trails | ❌ Limited | ✅ Complete |
| SSO Integration | ❌ No | ✅ Yes |
| Production Ready | ⚠️ Public only | ✅ Yes |
| Sensitive Data | ❌ Not recommended | ✅ Yes |

For production deployments with authentication, see the [secure-embed-chat-node](../secure-embed-chat-node) example which demonstrates:
- JWT-based authentication with RS256 signing
- User payload encryption using IBM's public key
- Context variable passing with user identity
- Secure cookie handling and token lifecycle management
- Key management and rotation procedures

## Additional Resources

- [Getting Started Guide](https://developer.watson-orchestrate.ibm.com/webchat/get_started)
- [Security Architecture](https://developer.watson-orchestrate.ibm.com/agents/integrate_agents#security-architecture)
- [Agent Integration Documentation](https://developer.watson-orchestrate.ibm.com/agents/integrate_agents)
