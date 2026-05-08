/**
 * ChatBubble — Single message in Zone A
 * Supports agent (left-aligned, glowing) and user (right-aligned) messages.
 */
const roleConfig = {
  agent: {
    align:  "flex-start",
    bg:     "rgba(59,130,246,0.1)",
    border: "1px solid rgba(59,130,246,0.2)",
    color:  "var(--color-text-primary)",
    label:  "C-IAW",
    labelColor: "#60a5fa",
    radius: "4px 16px 16px 16px",
  },
  user: {
    align:  "flex-end",
    bg:     "rgba(139,92,246,0.12)",
    border: "1px solid rgba(139,92,246,0.2)",
    color:  "var(--color-text-primary)",
    label:  "You",
    labelColor: "#a78bfa",
    radius: "16px 4px 16px 16px",
  },
};

function formatTime(iso) {
  try {
    return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  } catch { return ""; }
}

export default function ChatBubble({ message }) {
  const { role = "agent", content, timestamp } = message;
  const cfg = roleConfig[role] || roleConfig.agent;

  return (
    <div
      className="animate-fade-in-up"
      style={{ display: "flex", flexDirection: "column", alignItems: cfg.align, gap: 4 }}
    >
      {/* Sender label */}
      <span style={{ fontSize: "0.7rem", fontWeight: 600, color: cfg.labelColor, paddingInline: 4 }}>
        {cfg.label}
      </span>

      {/* Bubble */}
      <div
        style={{
          maxWidth: "88%",
          padding: "var(--space-3) var(--space-4)",
          background: cfg.bg,
          border: cfg.border,
          borderRadius: cfg.radius,
          backdropFilter: "blur(8px)",
        }}
      >
        <p style={{
          color: cfg.color,
          fontSize: "0.875rem",
          lineHeight: 1.65,
          whiteSpace: "pre-wrap",
          wordBreak: "break-word",
        }}>
          {content}
        </p>
      </div>

      {/* Timestamp */}
      {timestamp && (
        <span style={{ fontSize: "0.68rem", color: "var(--color-text-muted)", paddingInline: 4 }}>
          {formatTime(timestamp)}
        </span>
      )}
    </div>
  );
}
