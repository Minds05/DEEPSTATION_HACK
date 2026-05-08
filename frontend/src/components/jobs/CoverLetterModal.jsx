import { useState, useCallback } from "react";
import useAgentStore from "../../store/agentStore";
import api from "../../services/api";
import Spinner from "../common/Spinner";

/**
 * CoverLetterModal — Phase 6 UI
 * Generates, previews, and allows download of the Gemini-written cover letter.
 * Opens from Zone C JobCard → "Generate Cover Letter" button.
 */
export default function CoverLetterModal() {
  const modal                = useAgentStore((s) => s.coverLetterModal);
  const closeCoverLetterModal = useAgentStore((s) => s.closeCoverLetterModal);
  const setCoverLetterResult  = useAgentStore((s) => s.setCoverLetterResult);
  const setCoverLetterLoading = useAgentStore((s) => s.setCoverLetterLoading);
  const setCoverLetterError   = useAgentStore((s) => s.setCoverLetterError);

  const [copied, setCopied] = useState(false);

  const handleGenerate = useCallback(async () => {
    if (!modal.jobId) return;
    setCoverLetterLoading(true);
    try {
      const res = await api.post("/agent/cover-letter", { job_id: modal.jobId });
      setCoverLetterResult(res.data.cover_letter_text, res.data.cover_letter_url);
    } catch (err) {
      setCoverLetterError(err?.response?.data?.detail || "Generation failed.");
    }
  }, [modal.jobId, setCoverLetterLoading, setCoverLetterResult, setCoverLetterError]);

  const handleCopy = useCallback(() => {
    if (!modal.text) return;
    navigator.clipboard.writeText(modal.text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [modal.text]);

  if (!modal.open) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        onClick={closeCoverLetterModal}
        style={{
          position: "fixed", inset: 0, zIndex: 1000,
          background: "rgba(0,0,0,0.65)", backdropFilter: "blur(4px)",
        }}
      />

      {/* Modal panel */}
      <div
        className="animate-fade-in-up"
        style={{
          position: "fixed", inset: "5vh 5vw", zIndex: 1001,
          maxWidth: 720, margin: "0 auto",
          background: "rgba(13,19,32,0.97)",
          border: "1px solid var(--color-border-active)",
          borderRadius: "var(--radius-lg)",
          boxShadow: "var(--shadow-glow), var(--shadow-card)",
          display: "flex", flexDirection: "column",
          overflow: "hidden",
        }}
      >
        {/* Header */}
        <div style={{
          padding: "var(--space-4) var(--space-5)",
          borderBottom: "1px solid var(--color-border)",
          display: "flex", alignItems: "center", justifyContent: "space-between",
          flexShrink: 0,
        }}>
          <div>
            <h2 style={{ fontSize: "0.95rem", fontWeight: 700, marginBottom: 2 }}>
              Cover Letter
            </h2>
            {modal.jobTitle && (
              <p style={{ fontSize: "0.75rem", color: "var(--color-text-muted)" }}>
                {modal.jobTitle} — {modal.jobCompany}
              </p>
            )}
          </div>
          <button
            onClick={closeCoverLetterModal}
            style={{
              background: "none", border: "none", cursor: "pointer",
              color: "var(--color-text-muted)", fontSize: "1.25rem",
              padding: "var(--space-1)",
            }}
          >✕</button>
        </div>

        {/* Body */}
        <div style={{ flex: 1, overflowY: "auto", padding: "var(--space-5)" }}>
          {!modal.text && !modal.loading && !modal.error && (
            /* Generate CTA */
            <div style={{
              display: "flex", flexDirection: "column", alignItems: "center",
              gap: "var(--space-5)", padding: "var(--space-8)", textAlign: "center",
            }}>
              <div style={{ fontSize: "3rem" }}>✍️</div>
              <div>
                <p style={{ fontWeight: 700, color: "var(--color-text-primary)", marginBottom: 6 }}>
                  Generate a tailored cover letter with Gemini
                </p>
                <p style={{ fontSize: "0.8rem", color: "var(--color-text-muted)", lineHeight: 1.65 }}>
                  250 words · 3 paragraphs · tied to the job description
                </p>
              </div>
              <button
                onClick={handleGenerate}
                style={{
                  padding: "var(--space-3) var(--space-7)",
                  background: "linear-gradient(135deg,#3b82f6,#8b5cf6)",
                  border: "none", borderRadius: "var(--radius-md)",
                  color: "#fff", fontWeight: 700, fontSize: "0.9rem",
                  cursor: "pointer",
                }}
              >
                ✨ Generate Cover Letter
              </button>
            </div>
          )}

          {modal.loading && (
            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-4)", padding: "var(--space-8)" }}>
              <Spinner size={22} />
              <div>
                <p style={{ fontWeight: 600, color: "var(--color-text-primary)" }}>Writing your cover letter...</p>
                <p style={{ fontSize: "0.78rem", color: "var(--color-text-muted)" }}>Gemini 2.0 Flash is crafting it now</p>
              </div>
            </div>
          )}

          {modal.error && (
            <div style={{
              padding: "var(--space-4)", borderRadius: "var(--radius-md)",
              background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.2)",
            }}>
              <p style={{ color: "var(--color-error)", fontSize: "0.875rem" }}>❌ {modal.error}</p>
              <button
                onClick={handleGenerate}
                style={{ marginTop: "var(--space-3)", fontSize: "0.8rem", color: "#60a5fa",
                  background: "none", border: "none", cursor: "pointer" }}
              >
                Try again →
              </button>
            </div>
          )}

          {modal.text && !modal.loading && (
            /* Letter preview */
            <div style={{
              padding: "var(--space-5)",
              background: "rgba(255,255,255,0.03)",
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius-md)",
            }}>
              <pre style={{
                color: "var(--color-text-primary)",
                fontFamily: "var(--font-sans)", fontSize: "0.875rem",
                lineHeight: 1.75, whiteSpace: "pre-wrap", wordBreak: "break-word",
                margin: 0,
              }}>
                {modal.text}
              </pre>
            </div>
          )}
        </div>

        {/* Footer actions */}
        {modal.text && (
          <div style={{
            padding: "var(--space-4) var(--space-5)",
            borderTop: "1px solid var(--color-border)",
            display: "flex", gap: "var(--space-3)", flexShrink: 0,
          }}>
            <button
              onClick={handleCopy}
              style={{
                flex: 1, padding: "var(--space-2) var(--space-3)",
                background: copied ? "rgba(16,185,129,0.15)" : "rgba(255,255,255,0.05)",
                border: `1px solid ${copied ? "rgba(16,185,129,0.3)" : "var(--color-border)"}`,
                borderRadius: "var(--radius-sm)", cursor: "pointer",
                color: copied ? "#10b981" : "var(--color-text-secondary)",
                fontSize: "0.8rem", fontWeight: 600, transition: "all 0.2s",
              }}
            >
              {copied ? "✅ Copied!" : "📋 Copy Text"}
            </button>
            {modal.url && (
              <a
                href={modal.url} target="_blank" rel="noopener noreferrer"
                style={{
                  flex: 1, padding: "var(--space-2) var(--space-3)",
                  background: "linear-gradient(135deg,rgba(59,130,246,0.15),rgba(139,92,246,0.15))",
                  border: "1px solid rgba(99,179,237,0.25)",
                  borderRadius: "var(--radius-sm)", cursor: "pointer",
                  color: "var(--color-text-accent)", fontSize: "0.8rem", fontWeight: 600,
                  textDecoration: "none", textAlign: "center", display: "flex",
                  alignItems: "center", justifyContent: "center", gap: 4,
                }}
              >
                ⬇ Download PDF
              </a>
            )}
            <button
              onClick={handleGenerate}
              style={{
                padding: "var(--space-2) var(--space-3)",
                background: "rgba(255,255,255,0.03)",
                border: "1px solid var(--color-border)",
                borderRadius: "var(--radius-sm)", cursor: "pointer",
                color: "var(--color-text-muted)", fontSize: "0.8rem",
              }}
              title="Regenerate"
            >
              🔄
            </button>
          </div>
        )}
      </div>
    </>
  );
}
