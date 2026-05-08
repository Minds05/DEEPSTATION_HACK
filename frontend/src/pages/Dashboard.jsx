import AppShell from "../components/layout/AppShell";
import CoverLetterModal from "../components/jobs/CoverLetterModal";
import useAgentStore from "../store/agentStore";
import StatusPill from "../components/common/StatusPill";

/**
 * Dashboard — Main application page
 * Houses the top nav bar and the full three-zone AppShell.
 */
export default function Dashboard() {
  const taskStatus = useAgentStore((s) => s.taskStatus);

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column", overflow: "hidden" }}>
      {/* ── Top Navigation Bar ─────────────────────────────── */}
      <header style={{
        height: 52,
        display: "flex", alignItems: "center",
        justifyContent: "space-between",
        padding: "0 var(--space-5)",
        background: "rgba(8,12,20,0.85)",
        backdropFilter: "blur(16px)",
        borderBottom: "1px solid var(--color-border)",
        flexShrink: 0,
        zIndex: 100,
      }}>
        {/* Brand */}
        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)" }}>
          <div style={{
            width: 28, height: 28, borderRadius: 8, flexShrink: 0,
            background: "linear-gradient(135deg,#3b82f6,#8b5cf6)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: "0.85rem",
          }}>🤖</div>
          <div>
            <span style={{
              fontWeight: 800, fontSize: "0.9rem", letterSpacing: "0.02em",
              background: "linear-gradient(135deg,#60a5fa,#a78bfa)",
              WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
            }}>
              C-IAW
            </span>
            <span style={{
              marginLeft: 8, color: "var(--color-text-muted)",
              fontSize: "0.72rem", fontWeight: 500,
              display: window.innerWidth > 640 ? "inline" : "none",
            }}>
              Career Intelligence & Automation Worker
            </span>
          </div>
        </div>

        {/* Right side: agent status */}
        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)" }}>
          {taskStatus?.target && taskStatus.status !== "Idle" && (
            <span style={{
              fontSize: "0.72rem", color: "var(--color-text-muted)",
              fontFamily: "var(--font-mono)",
              display: window.innerWidth > 768 ? "block" : "none",
            }}>
              {taskStatus.agent} → {taskStatus.target}
            </span>
          )}
          <StatusPill
            status={taskStatus?.status || "Idle"}
            action={taskStatus?.last_action !== "Idle" ? taskStatus?.last_action : null}
          />
        </div>
      </header>

      {/* ── Three-Zone Dashboard ───────────────────────────── */}
      <main style={{ flex: 1, overflow: "hidden", minHeight: 0 }}>
        <AppShell />
      </main>

      {/* ── Global Modals ──────────────────────────── */}
      <CoverLetterModal />
    </div>
  );
}
