const express = require('express');
const path = require('path');
const { handleCreateJwt } = require('./create-jwt.js');

const PORT = 3100;
// Bind only to localhost; TLS termination is handled by the reverse proxy.
const HOST = '127.0.0.1';

// ── App setup ─────────────────────────────────────────────────────────────────

const app = express();
app.use(express.json());

// Serve the iframe HTML at the path OAuth will redirect back to. For production use, you'll probably want to add some cache control headers
// here to avoid re-downloading these files every time.
app.use(express.static(path.join(__dirname, '..', 'static')));

// ── POST /createJwt ───────────────────────────────────────────────────────────

app.post('/createJwt', handleCreateJwt);

// ── Start ─────────────────────────────────────────────────────────────────────

app.listen(PORT, HOST, () => {
    console.log(`Server running at http://${HOST}:${PORT}`);
});
