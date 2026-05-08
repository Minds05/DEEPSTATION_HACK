/**
 * Axios API service for the Housing module.
 * All requests go through the Housing Sub-Orchestrator backend.
 */
import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// ─── Request Interceptor ──────────────────────────────────────
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
  },
  (error) => Promise.reject(error)
);

// ─── Response Interceptor ─────────────────────────────────────
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const detail = error.response?.data?.detail || error.message;
    return Promise.reject(typeof detail === 'object' ? detail : { error: detail });
  }
);

// ─── Housing API (User Side) ──────────────────────────────────
export const housingApi = {
  /**
   * POST /api/housing/chat
   * Main conversational endpoint through the orchestrator.
   */
  chat: (query, userId, conversationId = null, history = []) =>
    api.post('/api/housing/chat', {
      query,
      user_id: userId,
      conversation_id: conversationId,
      history,
    }),

  /**
   * POST /api/housing/search
   * Structured search with explicit filters.
   */
  search: (filters) => api.post('/api/housing/search', filters),

  /**
   * POST /api/housing/recommend
   * Rank listings against user preferences.
   */
  recommend: (userPreferences, listings, userId) =>
    api.post('/api/housing/recommend', {
      user_preferences: userPreferences,
      listings,
      user_id: userId,
    }),

  /**
   * POST /api/housing/negotiate
   * Generate a negotiation message.
   */
  negotiate: (currentRent, targetRent, propertyType = 'flat') =>
    api.post('/api/housing/negotiate', {
      current_rent: currentRent,
      target_rent: targetRent,
      property_type: propertyType,
    }),

  /**
   * POST /api/housing/schedule
   * Book a property visit.
   */
  schedule: (propertyId, userId, slot, notes = null) =>
    api.post('/api/housing/schedule', {
      property_id: propertyId,
      user_id: userId,
      slot,
      notes,
    }),
};

export default api;
