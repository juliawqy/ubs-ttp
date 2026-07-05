const express = require("express");
const path = require("path");
const { createProxyMiddleware } = require("http-proxy-middleware");

const app = express();
const PORT = process.env.PORT || 3000;
const API_URL = process.env.API_URL || "http://localhost:8000";
const TRAINING_API_URL = process.env.TRAINING_API_URL || "http://localhost:8002";
const PERFORMANCE_API_URL = process.env.PERFORMANCE_API_URL || "http://localhost:8003";
const ANALYTICS_API_URL = process.env.ANALYTICS_API_URL || "http://localhost:8005";

// Serve static files (CSS, client-side JS)
app.use(express.static(path.join(__dirname, "../public")));

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

// ── API proxies ───────────────────────────────────────────────────────────────
// Specific service proxies must be registered BEFORE the generic /api fallback
// so Express picks the most specific match first.

app.use(
  "/api/training",
  createProxyMiddleware({
    target: TRAINING_API_URL,
    changeOrigin: true,
    pathRewrite: { "^/": "/training/" },
  })
);

app.use(
  "/api/performance",
  createProxyMiddleware({
    target: PERFORMANCE_API_URL,
    changeOrigin: true,
    pathRewrite: { "^/api/performance": "" },
  })
);

// /api/analytics → analytics service (/metrics/*)
app.use(
  "/api/analytics",
  createProxyMiddleware({
    target: ANALYTICS_API_URL,
    changeOrigin: true,
    pathRewrite: { "^/api/analytics": "" },
  })
);

// Generic fallback: remaining /api/* → recruitment api-gateway
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
