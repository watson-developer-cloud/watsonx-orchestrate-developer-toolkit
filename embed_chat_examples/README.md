# IBM watsonx Orchestrate Embed Chat Examples

This directory contains example implementations for integrating IBM watsonx Orchestrate embed chat into your applications.

## Available Examples

### 1. [Anonymous Embed Chat (Node.js)](./anonymous-embed-chat-node)

A simple, anonymous embed chat integration **without security enabled**.

**Use this when:**
- You're in development/testing phase
- Your chatbot is public-facing and doesn't require user authentication
- You're building a proof-of-concept
- No sensitive data or systems are accessed

**Quick start:**
```bash
cd anonymous-embed-chat-node
npm install
npm start
```

---

### 2. [Secure Embed Chat (Node.js)](./secure-embed-chat-node)

A secure embed chat implementation with JWT-based authentication and encryption.

**Use this when:**
- You need user authentication in production environments
- You want to pass user context securely to the chat
- You need to encrypt sensitive user data
- You're implementing SSO integration (On-Behalf-Of flow)
- Your instance accesses sensitive data or protected systems

**Quick start:**
```bash
cd secure-embed-chat-node
npm install
npm start
```

---

## Documentation

- [Getting Started with Embedded Chat](https://developer.watson-orchestrate.ibm.com/webchat/get_started)
- [Context Variables](https://developer.watson-orchestrate.ibm.com/webchat/context_variables)
- [Security Architecture](https://developer.watson-orchestrate.ibm.com/agents/integrate_agents#security-architecture)
- [IBM Docs: Securing Embedded Chat](https://www.ibm.com/docs/en/watsonx/watson-orchestrate/base?topic=applications-securing-embedded-chat)
- [Configuring security for embedded chat](https://www.ibm.com/docs/en/watsonx/watson-orchestrate/base?topic=chat-configuring-security-embedded)
- [Configuring security with scripting](https://www.ibm.com/docs/en/watsonx/watson-orchestrate/base?topic=chat-configuring-security-scripting)

## Quick Comparison

| Feature | Anonymous | Secure |
|---------|-----------|--------|
| User Authentication | ❌ No | ✅ Yes |
| JWT Required | ❌ No | ✅ Yes |
| Production Ready | ⚠️ Public only | ✅ Yes |
| Sensitive Data | ❌ Not recommended | ✅ Yes |

## Requirements

All examples require:
- Node.js version 16.15.1 or higher
- npm (Node Package Manager)
- OpenSSL (for key generation in secure mode)

## Support

For issues, questions, or contributions, please refer to the main project documentation or contact IBM watsonx Orchestrate support.