import { useRef, useEffect } from "react";
import ThoughtLog from "../chat/ThoughtLog";
import StatusPill from "../common/StatusPill";
import useAgentStore from "../../store/agentStore";

/**
 * Zone B — Activity Feed (center column)
 * Streams thought logs from Firestore in real-time.
 * Shows orchestrator task_status in the header.
 */
export default function ZoneB() {
  const thoughtLogs = useAgentStore((s) => s.thoughtLogs);
  const taskStatus  = useAgentStore((s) => s.taskStatus);
  const feedEndRef  = useRef(null);

  // Auto-scroll to newest log
  useEffect(() => {
    feedEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [thoughtLogs]);

  return (
    <div className="zone-b glass">
      {/* Header */}
      <div className="zone-header">
        <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          <h2>Activity Feed</h2>
          {taskStatus?.last_action && taskStatus.last_action !== "Idle" && (
            <p style={{ fontSize: "0.68rem", color: "var(--color-text-muted)", fontFamily: "var(--font-mono)" }}>
              Last: {taskStatus.last_action}
              {taskStatus.target ? ` → ${taskStatus.target}` : ""}
            </p>
          )}
        </div>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 4 }}>
          <span className="zone-badge">Zone B</span>
          <StatusPill status={taskStatus?.status || "Idle"} />
        </div>
      </div>

      {/* Feed body */}
      <div className="feed-body">
        {thoughtLogs.length === 0 ? (
          <EmptyFeed />
        ) : (
          [...thoughtLogs].reverse().map((log, idx) => (
            <ThoughtLog
              key={log.logId || idx}
              log={log}
              isNew={idx === thoughtLogs.length - 1}
            />
          ))
        )}
        <div ref={feedEndRef} />
      </div>
    </div>
  );
}

function EmptyFeed() {
  return (
    <div style={{
      flex: 1, display: "flex", flexDirection: "column",
      alignItems: "center", justifyContent: "center",
      gap: "var(--space-4)", padding: "var(--space-8)",
      color: "var(--color-text-muted)", textAlign: "center",
    }}>
      <div style={{ fontSize: "2.5rem", opacity: 0.4 }}>🧠</div>
      <div>
        <p style={{ fontWeight: 600, fontSize: "0.875rem", marginBottom: 4, color: "var(--color-text-secondary)" }}>
          Waiting for Agent
        </p>
        <p style={{ fontSize: "0.78rem", lineHeight: 1.6, fontFamily: "var(--font-mono)" }}>
          Thought logs will stream here<br />
          as C-IAW executes missions.
        </p>
      </div>
      {/* Idle animation dots */}
      <div style={{ display: "flex", gap: 6, opacity: 0.5 }}>
        <span className="typing-dot" style={{ background: "var(--color-text-muted)" }} />
        <span className="typing-dot" style={{ background: "var(--color-text-muted)" }} />
        <span className="typing-dot" style={{ background: "var(--color-text-muted)" }} />
      </div>
    </div>
  );
}
