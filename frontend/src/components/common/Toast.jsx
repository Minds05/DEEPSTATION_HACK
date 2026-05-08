import { useEffect, useState } from "react";

const TOAST_COLORS = {
  success: { bg: "rgba(16,185,129,0.12)", border: "rgba(16,185,129,0.3)", icon: "✅" },
  error:   { bg: "rgba(239,68,68,0.12)",  border: "rgba(239,68,68,0.3)",  icon: "❌" },
  warning: { bg: "rgba(245,158,11,0.12)", border: "rgba(245,158,11,0.3)", icon: "⚠️" },
  info:    { bg: "rgba(59,130,246,0.12)",  border: "rgba(59,130,246,0.3)", icon: "ℹ️" },
};

/**
 * Toast — ephemeral notification banner
 * Props: message, type ("success"|"error"|"warning"|"info"), duration (ms)
 */
export default function Toast({ message, type = "info", duration = 4000, onClose }) {
  const [visible, setVisible] = useState(true);
  const style = TOAST_COLORS[type] || TOAST_COLORS.info;

  useEffect(() => {
    const t = setTimeout(() => { setVisible(false); onClose?.(); }, duration);
    return () => clearTimeout(t);
  }, [duration, onClose]);

  if (!visible) return null;

  return (
    <div
      className="animate-fade-in-up"
      style={{
        position: "fixed", bottom: 24, right: 24, zIndex: 9999,
        display: "flex", alignItems: "center", gap: "var(--space-3)",
        padding: "var(--space-3) var(--space-5)",
        background: style.bg,
        border: `1px solid ${style.border}`,
        borderRadius: "var(--radius-md)",
        backdropFilter: "blur(12px)",
        boxShadow: "var(--shadow-card)",
        maxWidth: 380, minWidth: 260,
        fontFamily: "var(--font-sans)",
      }}
    >
      <span style={{ fontSize: "1.1rem" }}>{style.icon}</span>
      <p style={{ color: "var(--color-text-primary)", fontSize: "0.875rem", flex: 1 }}>
        {message}
      </p>
      <button
        onClick={() => { setVisible(false); onClose?.(); }}
        style={{
          background: "none", border: "none", cursor: "pointer",
          color: "var(--color-text-muted)", fontSize: "1rem", padding: 0,
        }}
      >✕</button>
    </div>
  );
}
