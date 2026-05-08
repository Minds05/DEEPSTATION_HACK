/**
 * StatusPill — Orchestrator task status indicator
 * Shows: Idle | Running | Success | Failed | Paused
 */
const STATUS_CONFIG = {
  Running: { color: "#3b82f6", bg: "rgba(59,130,246,0.12)", dot: true,  label: "Running"  },
  Success: { color: "#10b981", bg: "rgba(16,185,129,0.12)", dot: false, label: "Success"  },
  Failed:  { color: "#ef4444", bg: "rgba(239,68,68,0.12)",  dot: false, label: "Failed"   },
  Paused:  { color: "#f59e0b", bg: "rgba(245,158,11,0.12)", dot: true,  label: "Paused"   },
  Idle:    { color: "#475569", bg: "rgba(71,85,105,0.12)",  dot: false, label: "Idle"     },
};

export default function StatusPill({ status = "Idle", action = null }) {
  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.Idle;

  return (
    <div style={{
      display: "inline-flex", alignItems: "center", gap: 6,
      padding: "3px 10px",
      background: cfg.bg,
      border: `1px solid ${cfg.color}33`,
      borderRadius: 20,
      fontSize: "0.72rem", fontWeight: 600,
      fontFamily: "var(--font-sans)",
    }}>
      {/* Animated dot for active states */}
      {cfg.dot && (
        <span style={{
          width: 6, height: 6, borderRadius: "50%",
          background: cfg.color,
          animation: "statusPulse 1.5s ease-in-out infinite",
          flexShrink: 0,
        }} />
      )}
      <span style={{ color: cfg.color }}>{cfg.label}</span>
      {action && (
        <span style={{ color: "var(--color-text-muted)", marginLeft: 2 }}>
          · {action}
        </span>
      )}
    </div>
  );
}
