const cors = require('cors');
const express = require('express');
const path = require('path');
const { createJwt, handleCreateJwt } = require('./create-jwt.js');

const PORT = 3100;

// ── App setup ─────────────────────────────────────────────────────────────────

const app = express();
app.use(cors());
app.use(express.json());

// Serve the iframe HTML at the path OAuth will redirect back to. For production use, you'll probably want to add some cache control headers
// here to avoid re-downloading these files every time.
app.use(express.static(path.join(__dirname, '..', 'static')));

// ── POST /createJwt ───────────────────────────────────────────────────────────

app.post('/createJwt', handleCreateJwt);

// ── Start ─────────────────────────────────────────────────────────────────────

app.listen(PORT, () => {
    console.log(`Server running at http://localhost:${PORT}`);
});
