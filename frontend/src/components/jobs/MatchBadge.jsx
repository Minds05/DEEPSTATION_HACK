/**
 * MatchBadge — Score badge for job cards
 * Color coded: ≥92% green, 70–91% amber, <70% grey
 * Animated pop-in on mount.
 */
export default function MatchBadge({ score }) {
  const pct = Math.round(score ?? 0);

  let color, bg, border;
  if (pct >= 92) {
    color = "#10b981"; bg = "rgba(16,185,129,0.15)"; border = "rgba(16,185,129,0.35)";
  } else if (pct >= 70) {
    color = "#f59e0b"; bg = "rgba(245,158,11,0.15)"; border = "rgba(245,158,11,0.35)";
  } else {
    color = "#6b7280"; bg = "rgba(107,114,128,0.12)"; border = "rgba(107,114,128,0.25)";
  }

  return (
    <div
      className="animate-score-pop"
      style={{
        display: "inline-flex", alignItems: "center", gap: 4,
        padding: "4px 10px",
        background: bg, border: `1px solid ${border}`,
        borderRadius: 20,
        fontFamily: "var(--font-mono)",
        fontSize: "0.78rem", fontWeight: 700,
        color,
        letterSpacing: "0.02em",
        boxShadow: pct >= 92 ? `0 0 10px ${bg}` : "none",
        flexShrink: 0,
      }}
    >
      {pct >= 92 && <span style={{ fontSize: "0.7rem" }}>⚡</span>}
      {pct}%
    </div>
  );
}
