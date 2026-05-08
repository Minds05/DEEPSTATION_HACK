/**
 * ThoughtLog — Single Zone B activity feed entry
 * Type-colored icon + PII-safe message + timestamp
 */
const TYPE_CONFIG = {
  Thought: { icon: "💭", color: "#60a5fa", bg: "rgba(59,130,246,0.06)"  },
  Action:  { icon: "⚡", color: "#a78bfa", bg: "rgba(139,92,246,0.06)" },
  Success: { icon: "✅", color: "#10b981", bg: "rgba(16,185,129,0.06)" },
  Warning: { icon: "⚠️", color: "#f59e0b", bg: "rgba(245,158,11,0.06)" },
  Error:   { icon: "❌", color: "#ef4444", bg: "rgba(239,68,68,0.06)"  },
};

function formatTimestamp(ts) {
  if (!ts) return "";
  try {
    const d = ts?.toDate ? ts.toDate() : new Date(ts);
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  } catch { return ""; }
}

export default function ThoughtLog({ log, isNew = false }) {
  const { type = "Thought", message = "", timestamp } = log;
  const cfg = TYPE_CONFIG[type] || TYPE_CONFIG.Thought;

  return (
    <div
      className={`animate-fade-in-up ${isNew ? "animate-pulse-glow" : ""}`}
      style={{
        display: "flex", gap: "var(--space-3)", alignItems: "flex-start",
        padding: "var(--space-3) var(--space-4)",
        background: cfg.bg,
        border: `1px solid ${cfg.color}22`,
        borderLeft: `2px solid ${cfg.color}`,
        borderRadius: "0 var(--radius-sm) var(--radius-sm) 0",
        transition: "opacity var(--transition-normal)",
      }}
    >
      {/* Icon */}
      <span style={{ fontSize: "0.875rem", flexShrink: 0, marginTop: 1 }}>{cfg.icon}</span>

      {/* Content */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <p style={{
          color: "var(--color-text-primary)",
          fontSize: "0.78rem",
          fontFamily: "var(--font-mono)",
          lineHeight: 1.55,
          wordBreak: "break-word",
          whiteSpace: "pre-wrap",
        }}>
          {message}
        </p>
        {timestamp && (
          <span style={{ color: "var(--color-text-muted)", fontSize: "0.68rem", fontFamily: "var(--font-mono)" }}>
            {formatTimestamp(timestamp)}
          </span>
        )}
      </div>
    </div>
  );
}
