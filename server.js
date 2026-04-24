require('dotenv').config();
const express = require('express');
const app = express();

// Serve all static files (your HTML, CSS, JS) from current folder
app.use(express.static('.'));

// Endpoint to safely pass the API key to the frontend
app.get('/api/key', (req, res) => {
  const key = process.env.GEMINI_API_KEY;
  if (!key) {
    return res.status(500).json({ error: 'GEMINI_API_KEY not set in .env file' });
  }
  res.json({ key });
});

// Endpoint for Google Maps key
app.get('/api/maps-key', (req, res) => {
  const key = process.env.GOOGLE_MAPS_API_KEY;
  if (!key) {
    return res.status(500).json({ error: 'GOOGLE_MAPS_API_KEY not set in .env file' });
  }
  res.json({ key });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`✅ AgroSignal running at http://localhost:${PORT}`);
});
