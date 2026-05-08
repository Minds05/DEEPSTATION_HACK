import { useState, useMemo } from "react";
import JobCard from "../jobs/JobCard";
import useAgentStore from "../../store/agentStore";

const FILTERS = [
  { key: "ALL",              label: "All" },
  { key: "AUTO_APPLY",      label: "⚡ Auto-Apply" },
  { key: "MANUAL_REQUIRED", label: "✍️ Manual" },
  { key: "RECOMMENDATION",  label: "★ Recommended" },
];

/**
 * Zone C — Job Vault (right column)
 * Displays all jobs from job_pool with filter tabs and live stats.
 * Firestore listener is mounted in AppShell.
 */
export default function ZoneC() {
  const jobs          = useAgentStore((s) => s.jobs);
  const [filter, setFilter] = useState("ALL");

  const filtered = useMemo(() => {
    if (filter === "ALL") return jobs;
    return jobs.filter((j) => j.decision === filter);
  }, [jobs, filter]);

  // Counts per category
  const counts = useMemo(() => ({
    ALL:              jobs.length,
    AUTO_APPLY:       jobs.filter((j) => j.decision === "AUTO_APPLY").length,
    MANUAL_REQUIRED:  jobs.filter((j) => j.decision === "MANUAL_REQUIRED").length,
    RECOMMENDATION:   jobs.filter((j) => j.decision === "RECOMMENDATION").length,
  }), [jobs]);

  return (
    <div className="zone-c glass">
      {/* Header */}
      <div className="zone-header">
        <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          <h2>Job Vault</h2>
          <p style={{ fontSize: "0.68rem", color: "var(--color-text-muted)", fontFamily: "var(--font-mono)" }}>
            {jobs.length} job{jobs.length !== 1 ? "s" : ""} discovered
          </p>
        </div>
        <span className="zone-badge">Zone C</span>
      </div>

      {/* Stats bar */}
      {jobs.length > 0 && (
        <div style={{
          display: "grid", gridTemplateColumns: "repeat(3, 1fr)",
          gap: "var(--space-2)", padding: "var(--space-3) var(--space-4)",
          borderBottom: "1px solid var(--color-border)",
        }}>
          <StatChip value={counts.AUTO_APPLY} label="Auto-Apply" color="#10b981" />
          <StatChip value={counts.MANUAL_REQUIRED} label="Manual" color="#f59e0b" />
          <StatChip value={counts.RECOMMENDATION} label="Suggest." color="#6b7280" />
        </div>
      )}

      {/* Filter tabs */}
      <div style={{
        display: "flex", gap: "var(--space-1)",
        padding: "var(--space-3) var(--space-4)",
        borderBottom: "1px solid var(--color-border)",
        flexWrap: "wrap",
      }}>
        {FILTERS.map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setFilter(key)}
            style={{
              padding: "3px 10px",
              borderRadius: 20, border: "none", cursor: "pointer",
              fontSize: "0.72rem", fontWeight: 600,
              fontFamily: "var(--font-sans)",
              transition: "all var(--transition-fast)",
              background: filter === key
                ? "linear-gradient(135deg,#3b82f6,#8b5cf6)"
                : "rgba(255,255,255,0.04)",
              color: filter === key ? "#fff" : "var(--color-text-muted)",
            }}
          >
            {label}
            {counts[key] > 0 && (
              <span style={{ marginLeft: 5, opacity: 0.7 }}>({counts[key]})</span>
            )}
          </button>
        ))}
      </div>

      {/* Job list */}
      <div className="vault-body">
        {filtered.length === 0 ? (
          <EmptyVault hasJobs={jobs.length > 0} filter={filter} />
        ) : (
          filtered.map((job, idx) => (
            <JobCard key={job.jobId || idx} job={job} />
          ))
        )}
      </div>
    </div>
  );
}

function StatChip({ value, label, color }) {
  return (
    <div style={{
      textAlign: "center", padding: "var(--space-2)",
      background: `${color}10`, border: `1px solid ${color}25`,
      borderRadius: "var(--radius-sm)",
    }}>
      <p style={{ fontSize: "1.1rem", fontWeight: 800, color, lineHeight: 1 }}>{value}</p>
      <p style={{ fontSize: "0.62rem", color: "var(--color-text-muted)", marginTop: 2 }}>{label}</p>
    </div>
  );
}

function EmptyVault({ hasJobs, filter }) {
  return (
    <div style={{
      flex: 1, display: "flex", flexDirection: "column",
      alignItems: "center", justifyContent: "center",
      gap: "var(--space-4)", padding: "var(--space-8)",
      color: "var(--color-text-muted)", textAlign: "center",
    }}>
      <div style={{ fontSize: "2.5rem", opacity: 0.4 }}>
        {hasJobs ? "🔍" : "💼"}
      </div>
      <div>
        <p style={{ fontWeight: 600, fontSize: "0.875rem", marginBottom: 4, color: "var(--color-text-secondary)" }}>
          {hasJobs ? `No ${filter.replace("_", " ").toLowerCase()} jobs` : "Vault is empty"}
        </p>
        <p style={{ fontSize: "0.78rem", lineHeight: 1.6 }}>
          {hasJobs
            ? "Try a different filter tab."
            : "Parse your resume, then start a job hunt\nto populate the vault."}
        </p>
      </div>
    </div>
  );
}
