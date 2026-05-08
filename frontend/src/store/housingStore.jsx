/**
 * Housing state store using React Context + useReducer.
 * Maintains: messages, listings, recommendations, schedules.
 */
import { createContext, useContext, useReducer, useCallback } from 'react';
import { housingApi } from '../services/api';
import { generateDummyData } from './dummyData';

const dummyListings = generateDummyData();

// ─── Initial State ────────────────────────────────────────────
const initialState = {
  messages: [],
  listings: dummyListings,
  recommendations: [],
  schedules: [],
  preferences: {},
  isLoading: false,
  error: null,
  conversationId: null,
  searchMeta: { total: dummyListings.length, page: 1, source: 'fallback' },
};

// ─── Action Types ─────────────────────────────────────────────
const ACTIONS = {
  SET_LOADING: 'SET_LOADING',
  SET_ERROR: 'SET_ERROR',
  ADD_MESSAGE: 'ADD_MESSAGE',
  SET_LISTINGS: 'SET_LISTINGS',
  SET_RECOMMENDATIONS: 'SET_RECOMMENDATIONS',
  ADD_SCHEDULE: 'ADD_SCHEDULE',
  SET_PREFERENCES: 'SET_PREFERENCES',
  SET_CONVERSATION_ID: 'SET_CONVERSATION_ID',
  CLEAR_ERROR: 'CLEAR_ERROR',
};

// ─── Reducer ──────────────────────────────────────────────────
function housingReducer(state, action) {
  switch (action.type) {
    case ACTIONS.SET_LOADING:
      return { ...state, isLoading: action.payload };
    case ACTIONS.SET_ERROR:
      return { ...state, error: action.payload, isLoading: false };
    case ACTIONS.CLEAR_ERROR:
      return { ...state, error: null };
    case ACTIONS.ADD_MESSAGE:
      return { ...state, messages: [...state.messages, action.payload] };
    case ACTIONS.SET_LISTINGS:
      return {
        ...state,
        listings: action.payload.results || [],
        searchMeta: {
          total: action.payload.total || 0,
          page: action.payload.page || 1,
          source: action.payload.source || 'fallback',
        },
      };
    case ACTIONS.SET_RECOMMENDATIONS:
      return { ...state, recommendations: action.payload.recommendations || [] };
    case ACTIONS.ADD_SCHEDULE:
      return { ...state, schedules: [...state.schedules, action.payload] };
    case ACTIONS.SET_PREFERENCES:
      return { ...state, preferences: action.payload };
    case ACTIONS.SET_CONVERSATION_ID:
      return { ...state, conversationId: action.payload };
    default:
      return state;
  }
}

// ─── Context ──────────────────────────────────────────────────
const HousingContext = createContext(null);

export function HousingProvider({ children }) {
  const [state, dispatch] = useReducer(housingReducer, initialState);

  const userId = 'user_demo_01'; // In production: from Firebase Auth

  /**
   * Send a chat message through the orchestrator.
   * Handles the full search → recommend pipeline.
   */
  const sendMessage = useCallback(async (query) => {
    // Optimistically add user message
    dispatch({ type: ACTIONS.ADD_MESSAGE, payload: { role: 'user', content: query, id: Date.now() } });
    dispatch({ type: ACTIONS.SET_LOADING, payload: true });
    dispatch({ type: ACTIONS.CLEAR_ERROR });

    try {
      const result = await housingApi.chat(query, userId, state.conversationId, state.messages);

      // Update conversation ID
      if (result.conversation_id) {
        dispatch({ type: ACTIONS.SET_CONVERSATION_ID, payload: result.conversation_id });
      }

      const response = result.response || {};

      // Extract listings and recommendations from orchestrator response
      if (response.search?.results) {
        dispatch({ type: ACTIONS.SET_LISTINGS, payload: response.search });
      }
      if (response.recommendations?.recommendations) {
        dispatch({ type: ACTIONS.SET_RECOMMENDATIONS, payload: response.recommendations });
      }
      if (response.preferences) {
        dispatch({ type: ACTIONS.SET_PREFERENCES, payload: response.preferences });
      }

      // Add assistant response message
      const assistantMsg = buildAssistantMessage(result);
      dispatch({ type: ACTIONS.ADD_MESSAGE, payload: assistantMsg });

    } catch (err) {
      dispatch({ type: ACTIONS.SET_ERROR, payload: err.error || 'Something went wrong' });
      dispatch({
        type: ACTIONS.ADD_MESSAGE,
        payload: { role: 'assistant', content: null, error: err.error || 'Failed to process request', id: Date.now() + 1 },
      });
    } finally {
      dispatch({ type: ACTIONS.SET_LOADING, payload: false });
    }
  }, [state.conversationId, state.messages]);

  /**
   * Direct search with explicit filters.
   */
  const searchListings = useCallback(async (filters) => {
    dispatch({ type: ACTIONS.SET_LOADING, payload: true });
    try {
      const result = await housingApi.search(filters);
      dispatch({ type: ACTIONS.SET_LISTINGS, payload: result });
    } catch (err) {
      dispatch({ type: ACTIONS.SET_ERROR, payload: err.error || 'Search failed' });
    } finally {
      dispatch({ type: ACTIONS.SET_LOADING, payload: false });
    }
  }, []);

  /**
   * Book a property visit.
   */
  const scheduleVisit = useCallback(async (propertyId, slot, notes = null) => {
    dispatch({ type: ACTIONS.SET_LOADING, payload: true });
    try {
      const result = await housingApi.schedule(propertyId, userId, slot, notes);
      dispatch({ type: ACTIONS.ADD_SCHEDULE, payload: result });
      return result;
    } catch (err) {
      dispatch({ type: ACTIONS.SET_ERROR, payload: err.error || 'Scheduling failed' });
      throw err;
    } finally {
      dispatch({ type: ACTIONS.SET_LOADING, payload: false });
    }
  }, []);

  /**
   * Get negotiation message for a listing.
   */
  const getNegotiationMessage = useCallback(async (currentRent, targetRent, propertyType) => {
    try {
      return await housingApi.negotiate(currentRent, targetRent, propertyType);
    } catch (err) {
      throw err;
    }
  }, []);

  return (
    <HousingContext.Provider value={{
      ...state,
      sendMessage,
      searchListings,
      scheduleVisit,
      getNegotiationMessage,
    }}>
      {children}
    </HousingContext.Provider>
  );
}

export function useHousing() {
  const ctx = useContext(HousingContext);
  if (!ctx) throw new Error('useHousing must be used within HousingProvider');
  return ctx;
}

// ─── Helpers ──────────────────────────────────────────────────
function buildAssistantMessage(result) {
  const response = result.response || {};
  const task = result.task || 'recommend';
  const total = response.search?.total || 0;
  const recs = response.recommendations?.recommendations?.length || 0;

  return {
    id: Date.now() + 1,
    role: 'assistant',
    task,
    content: null, // Rendered by ChatPanel based on task
    data: response,
    meta: { total, recommendations: recs, agent_trace: result.agent_trace || [] },
  };
}
