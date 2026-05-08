// Axios instance pre-configured for the FastAPI backend
import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
  timeout: 30000,
  headers: { "Content-Type": "application/json" },
});

// ── Request interceptor: attach user_id to every request ──────
api.interceptors.request.use((config) => {
  const userId = import.meta.env.VITE_USER_ID || "local_user";
  if (config.params) {
    config.params.user_id = userId;
  } else {
    config.params = { user_id: userId };
  }
  return config;
});

// ── Response interceptor: surface errors as toasts (Phase 4) ──
api.interceptors.response.use(
  (res) => res,
  (err) => {
    console.error("[C-IAW API Error]", err?.response?.data || err.message);
    return Promise.reject(err);
  }
);

export default api;
