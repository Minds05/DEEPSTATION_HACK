import MatchBadge from "./MatchBadge";
import useAgentStore from "../../store/agentStore";

/**
 * JobCard — Zone C job listing card
 * Shows: title, company, ATS type badge, match score,
 * decision chip, reasoning snippet, and action button.
 */

const DECISION_CONFIG = {
  AUTO_APPLY:      { label: "Auto-Apply",   color: "#10b981", bg: "rgba(16,185,129,0.12)",  border: "rgba(16,185,129,0.25)" },
  MANUAL_REQUIRED: { label: "Manual Apply", color: "#f59e0b", bg: "rgba(245,158,11,0.12)",  border: "rgba(245,158,11,0.25)" },
  RECOMMENDATION:  { label: "Recommended",  color: "#6b7280", bg: "rgba(107,114,128,0.1)",  border: "rgba(107,114,128,0.2)" },
};

const ATS_LABELS = {
  lever:      { label: "Lever ⚡",      color: "#60a5fa" },
  greenhouse: { label: "Greenhouse ⚡", color: "#34d399" },
  workday:    { label: "Workday ✍️",    color: "#f59e0b" },
  other:      { label: "Other ✍️",      color: "#9ca3af" },
};

export default function JobCard({ job }) {
  const {
    title, company, url,
    matchScore, decision,
    atsType, reasoningSummary,
  } = job;

  const decisionCfg = DECISION_CONFIG[decision] || DECISION_CONFIG.RECOMMENDATION;
  const atsCfg = ATS_LABELS[atsType] || ATS_LABELS.other;
  const isAutoApply   = decision === "AUTO_APPLY";
  const isManual      = decision === "MANUAL_REQUIRED";

  const openCoverLetterModal = useAgentStore((s) => s.openCoverLetterModal);

  return (
    <div
      className="glass animate-slide-in-right stagger-item"
      style={{
        padding: "var(--space-4)",
        borderRadius: "var(--radius-md)",
        display: "flex", flexDirection: "column", gap: "var(--space-3)",
        transition: "all var(--transition-normal)",
        cursor: "pointer",
        position: "relative", overflow: "hidden",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = "translateY(-2px)";
        e.currentTarget.style.borderColor = "var(--color-border-active)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = "translateY(0)";
        e.currentTarget.style.borderColor = "var(--color-border)";
      }}
    >
      {/* Top stripe accent for perfect matches */}
      {isAutoApply && (
        <div style={{
          position: "absolute", top: 0, left: 0, right: 0, height: 2,
          background: "linear-gradient(90deg, #10b981, #3b82f6)",
        }} />
      )}

      {/* Row 1: Title + Score */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "var(--space-2)" }}>
        <div style={{ minWidth: 0 }}>
          <h3 style={{
            fontSize: "0.875rem", fontWeight: 700,
            color: "var(--color-text-primary)",
            lineHeight: 1.3, marginBottom: 2,
            overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
          }}>
            {title}
          </h3>
          <p style={{ color: "var(--color-text-secondary)", fontSize: "0.78rem", fontWeight: 500 }}>
            {company}
          </p>
          <div style={{ display: "flex", gap: "var(--space-2)", marginTop: 4, alignItems: "center" }}>
            {job.location && (
              <span style={{ fontSize: "0.7rem", color: "var(--color-text-muted)" }}>
                📍 {job.location}
              </span>
            )}
            {job.package && (
              <span style={{ fontSize: "0.7rem", color: "var(--color-text-muted)", background: "rgba(255,255,255,0.05)", padding: "1px 6px", borderRadius: 4 }}>
                💰 {job.package}
              </span>
            )}
          </div>
        </div>
        <MatchBadge score={matchScore} />
      </div>

      {/* Row 2: ATS + Decision chips */}
      <div style={{ display: "flex", gap: "var(--space-2)", flexWrap: "wrap" }}>
        {/* ATS Badge */}
        <span style={{
          fontSize: "0.68rem", fontWeight: 600, padding: "2px 8px",
          borderRadius: 20, background: `${atsCfg.color}15`,
          border: `1px solid ${atsCfg.color}30`, color: atsCfg.color,
        }}>
          {atsCfg.label}
        </span>

        {/* Decision Badge */}
        <span style={{
          fontSize: "0.68rem", fontWeight: 600, padding: "2px 8px",
          borderRadius: 20,
          background: decisionCfg.bg,
          border: `1px solid ${decisionCfg.border}`,
          color: decisionCfg.color,
        }}>
          {decisionCfg.label}
        </span>
      </div>

      {/* Row 3: Reasoning snippet */}
      {reasoningSummary && (
        <p style={{
          color: "var(--color-text-muted)", fontSize: "0.75rem",
          lineHeight: 1.55, display: "-webkit-box",
          WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden",
        }}>
          {reasoningSummary}
        </p>
      )}

      {/* Row 4: Action buttons */}
      <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-2)" }}>
        <a
          href={url} target="_blank" rel="noopener noreferrer"
          onClick={(e) => e.stopPropagation()}
          style={{
            display: "flex", alignItems: "center", justifyContent: "center",
            gap: "var(--space-2)",
            padding: "var(--space-2) var(--space-3)",
            background: isAutoApply
              ? "linear-gradient(135deg, rgba(16,185,129,0.15), rgba(59,130,246,0.15))"
              : "rgba(255,255,255,0.04)",
            border: `1px solid ${decisionCfg.border}`,
            borderRadius: "var(--radius-sm)",
            color: decisionCfg.color,
            fontSize: "0.75rem", fontWeight: 600,
            textDecoration: "none",
            transition: "all var(--transition-fast)",
          }}
          onMouseEnter={(e) => e.currentTarget.style.opacity = "0.8"}
          onMouseLeave={(e) => e.currentTarget.style.opacity = "1"}
        >
          {isAutoApply ? "⚡ View & Auto-Apply" : "↗ View Listing"}
        </a>

        {/* Cover Letter button — only for MANUAL_REQUIRED */}
        {isManual && (
          <button
            onClick={(e) => { e.stopPropagation(); openCoverLetterModal(job); }}
            style={{
              display: "flex", alignItems: "center", justifyContent: "center",
              gap: "var(--space-2)",
              padding: "var(--space-2) var(--space-3)",
              background: job.coverLetterUrl
                ? "rgba(16,185,129,0.08)"
                : "rgba(245,158,11,0.08)",
              border: `1px solid ${job.coverLetterUrl ? "rgba(16,185,129,0.25)" : "rgba(245,158,11,0.2)"}`,
              borderRadius: "var(--radius-sm)", cursor: "pointer",
              color: job.coverLetterUrl ? "#10b981" : "#f59e0b",
              fontSize: "0.72rem", fontWeight: 600,
              transition: "all var(--transition-fast)",
              fontFamily: "var(--font-sans)",
            }}
          >
            {job.coverLetterUrl ? "✅ Cover Letter Ready" : "✍️ Generate Cover Letter"}
          </button>
        )}
      </div>
    </div>
  );
}

