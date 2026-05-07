const express = require("express");
const path = require("path");
const { createProxyMiddleware } = require("http-proxy-middleware");

const app = express();
const PORT = process.env.PORT || 3000;
const API_URL = process.env.API_URL || "http://localhost:8000";

// Serve static files (CSS, client-side JS)
app.use(express.static(path.join(__dirname, "../public")));
app.use(express.json());

// ── Pages ───────────────────────────────────────────────────────────────────
app.get("/", (req, res) => {
  res.sendFile(path.join(__dirname, "../views/index.html"));
});

app.get("/hiring", (req, res) => {
  res.sendFile(path.join(__dirname, "../views/hiring/index.html"));
});

app.get("/training", (req, res) => {
  res.sendFile(path.join(__dirname, "../views/training/index.html"));
});

app.get("/performance", (req, res) => {
  res.sendFile(path.join(__dirname, "../views/performance/index.html"));
});

app.get("/dashboard", (req, res) => {
  res.sendFile(path.join(__dirname, "../views/dashboard/index.html"));
});

// ── Health check ─────────────────────────────────────────────────────────────
app.get("/health", (req, res) => {
  res.json({ status: "ok", service: "frontend" });
});

// ── API proxy ─────────────────────────────────────────────────────────────────
// Proxies /api/* to the api-gateway. API_URL is set via env var.
app.use(
  "/api",
  createProxyMiddleware({
    target: API_URL,
    changeOrigin: true,
    pathRewrite: { "^/api": "" },
  })
);

app.listen(PORT, () => {
  console.log("Frontend running on http://localhost:" + PORT);
});
