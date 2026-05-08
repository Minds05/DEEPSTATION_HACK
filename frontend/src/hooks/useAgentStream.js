/**
 * useAgentStream — SSE consumer for Zone B thought logs (Phase 7)
 *
 * Connects to GET /agent/stream and pushes thought log events
 * into Zustand store in real-time.
 * Falls back gracefully if the stream is unavailable.
 */
import { useEffect, useRef } from "react";
import useAgentStore from "../store/agentStore";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const USER_ID  = import.meta.env.VITE_USER_ID || "local_user";

export function useAgentStream(enabled = false) {
  const addThoughtLog  = useAgentStore((s) => s.addThoughtLog);
  const setTaskStatus  = useAgentStore((s) => s.setTaskStatus);
  const eventSourceRef = useRef(null);

  useEffect(() => {
    if (!enabled) return;

    const url = `${API_BASE}/agent/stream?user_id=${USER_ID}`;
    const es  = new EventSource(url);
    eventSourceRef.current = es;

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        // Thought log event → Zone B
        if (data.type && data.message) {
          addThoughtLog({
            logId:     Date.now().toString(),
            type:      data.type,
            message:   data.message,
            timestamp: data.timestamp || new Date().toISOString(),
            jobId:     data.job_id,
            appId:     data.app_id,
          });
        }

        // Task status update → global header
        if (data.status && data.agent) {
          setTaskStatus(data);
        }
      } catch (err) {
        console.warn("[useAgentStream] Parse error:", err);
      }
    };

    es.onerror = () => {
      console.warn("[useAgentStream] SSE connection lost. Will retry.");
      es.close();
    };

    return () => {
      es.close();
      eventSourceRef.current = null;
    };
  }, [enabled, addThoughtLog, setTaskStatus]);

  const disconnect = () => {
    eventSourceRef.current?.close();
  };

  return { disconnect };
}
