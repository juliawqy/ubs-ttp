/**
 * api.js — shared fetch wrapper for all pages
 * All requests go through /api/* which the Express server proxies to the api-gateway.
 */

const API_BASE = "/api";

async function apiFetch(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    const detail = err.detail;
    const message = Array.isArray(detail)
      ? detail.map((e) => e.msg || JSON.stringify(e)).join('; ')
      : (detail || 'API error');
    throw new Error(message);
  }
  if (res.status === 204) return null;
  return res.json();
}

// Convenience wrappers
const api = {
  get: (path) => apiFetch(path),
  post: (path, body) => apiFetch(path, { method: "POST", body: JSON.stringify(body) }),
  put: (path, body) => apiFetch(path, { method: "PUT", body: JSON.stringify(body) }),
  patch: (path, body) => apiFetch(path, { method: "PATCH", body: JSON.stringify(body) }),
  delete: (path) => apiFetch(path, { method: "DELETE" }),
};

// Make available globally
window.api = api;
