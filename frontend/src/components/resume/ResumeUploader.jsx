/**
 * ResumeUploader — Drag-and-drop PDF upload component
 * Handles file selection, validation, and upload/parse flow.
 * Integrates with useResumeUpload hook.
 */
import React, { useRef, useState, useCallback } from "react";
import { useResumeUpload } from "../../hooks/useResumeUpload";
import useAgentStore from "../../store/agentStore";

const STATE_LABELS = {
  idle:      "Drop your resume here or click to browse",
  uploading: "Uploading to Firebase Storage...",
  parsing:   "Gemini 2.0 Flash is reading your resume...",
  done:      "Resume parsed successfully ✓",
  error:     "Upload failed — try again",
};

const STATE_COLORS = {
  idle:      "var(--color-border)",
  uploading: "var(--color-primary)",
  parsing:   "var(--color-secondary)",
  done:      "var(--color-match-high)",
  error:     "var(--color-error)",
};

export default function ResumeUploader() {
  const fileInputRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);
  const { uploadState, error, resumeUrl, uploadAndParse, reset } = useResumeUpload();
  const userProfile = useAgentStore((s) => s.userProfile);

  const handleFile = useCallback(
    (file) => {
      if (file?.type === "application/pdf") {
        uploadAndParse(file);
      }
    },
    [uploadAndParse]
  );

  const onDrop = useCallback(
    (e) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      handleFile(file);
    },
    [handleFile]
  );

  const onDragOver = (e) => { e.preventDefault(); setIsDragging(true); };
  const onDragLeave = () => setIsDragging(false);
  const onInputChange = (e) => handleFile(e.target.files[0]);
  const onClick = () => uploadState === "idle" && fileInputRef.current?.click();

  const isLoading = uploadState === "uploading" || uploadState === "parsing";
  const borderColor = isDragging
    ? "var(--color-primary)"
    : STATE_COLORS[uploadState] || STATE_COLORS.idle;

  return (
    <div style={{ width: "100%" }}>
      {/* Drop Zone */}
      <div
        onClick={onClick}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        style={{
          border: `2px dashed ${borderColor}`,
          borderRadius: "var(--radius-lg)",
          padding: "var(--space-8) var(--space-6)",
          textAlign: "center",
          cursor: isLoading || uploadState === "done" ? "default" : "pointer",
          transition: "all var(--transition-normal)",
          background: isDragging
            ? "var(--color-primary-glow)"
            : "rgba(13,19,32,0.5)",
          position: "relative",
          overflow: "hidden",
        }}
      >
        {/* Animated background shimmer during loading */}
        {isLoading && (
          <div
            style={{
              position: "absolute", inset: 0,
              background:
                "linear-gradient(90deg, transparent 0%, rgba(59,130,246,0.08) 50%, transparent 100%)",
              animation: "shimmer 1.5s ease-in-out infinite",
            }}
          />
        )}

        {/* Icon */}
        <div style={{ fontSize: "2.5rem", marginBottom: "var(--space-3)" }}>
          {uploadState === "done"  ? "✅" :
           uploadState === "error" ? "❌" :
           isLoading               ? <div className="spinner" style={{ margin: "0 auto" }} /> :
           "📄"}
        </div>

        {/* Label */}
        <p style={{
          color: uploadState === "error"
            ? "var(--color-error)"
            : "var(--color-text-secondary)",
          fontSize: "0.875rem",
          fontWeight: 500,
          marginBottom: "var(--space-2)",
        }}>
          {STATE_LABELS[uploadState]}
        </p>

        {/* Sub-label */}
        {uploadState === "idle" && (
          <p style={{ color: "var(--color-text-muted)", fontSize: "0.75rem" }}>
            PDF only · Max 10 MB
          </p>
        )}

        {/* Parse progress indicator */}
        {uploadState === "parsing" && (
          <div style={{
            display: "flex", alignItems: "center", justifyContent: "center",
            gap: "var(--space-2)", marginTop: "var(--space-3)"
          }}>
            <span className="typing-dot" />
            <span className="typing-dot" />
            <span className="typing-dot" />
          </div>
        )}

        <input
          ref={fileInputRef}
          type="file"
          accept="application/pdf"
          onChange={onInputChange}
          style={{ display: "none" }}
        />
      </div>

      {/* Error message */}
      {error && (
        <p style={{
          color: "var(--color-error)",
          fontSize: "0.75rem",
          marginTop: "var(--space-2)",
          padding: "var(--space-2) var(--space-3)",
          background: "rgba(239,68,68,0.08)",
          borderRadius: "var(--radius-sm)",
          border: "1px solid rgba(239,68,68,0.2)",
        }}>
          {error}
        </p>
      )}

      {/* Success — profile summary chip */}
      {uploadState === "done" && userProfile && (
        <div
          className="animate-fade-in-up"
          style={{
            marginTop: "var(--space-3)",
            padding: "var(--space-3) var(--space-4)",
            background: "var(--color-match-high-bg)",
            border: "1px solid rgba(16,185,129,0.25)",
            borderRadius: "var(--radius-md)",
            display: "flex",
            flexDirection: "column",
            gap: "var(--space-1)",
          }}
        >
          <p style={{ color: "var(--color-match-high)", fontWeight: 700, fontSize: "0.8rem" }}>
            {userProfile.name} · {userProfile.seniority}
          </p>
          <p style={{ color: "var(--color-text-muted)", fontSize: "0.72rem" }}>
            {userProfile.skills?.slice(0, 5).join(" · ")}
            {userProfile.skills?.length > 5 ? ` +${userProfile.skills.length - 5} more` : ""}
          </p>
        </div>
      )}

      {/* Re-upload button */}
      {(uploadState === "done" || uploadState === "error") && (
        <button
          onClick={reset}
          className="btn btn-ghost"
          style={{ width: "100%", marginTop: "var(--space-3)", fontSize: "0.8rem" }}
        >
          Upload a different resume
        </button>
      )}
    </div>
  );
}
