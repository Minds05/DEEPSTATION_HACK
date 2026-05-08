import { useState, useRef, useCallback } from "react";
import Spinner from "../common/Spinner";

/**
 * ChatInput — Zone A message input
 * Handles free-form chat, sends messages to the agent store,
 * and triggers job searches via the API.
 */
export default function ChatInput({ onSend, onJobSearch, disabled = false }) {
  const [text, setText] = useState("");
  const [searching, setSearching] = useState(false);
  const inputRef = useRef(null);

  const handleSend = useCallback(() => {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend?.(trimmed);
    setText("");
    inputRef.current?.focus();
  }, [text, disabled, onSend]);

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleJobSearch = async () => {
    if (searching || disabled) return;
    setSearching(true);
    try { await onJobSearch?.(); }
    finally { setSearching(false); }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-2)" }}>

      {/* Text row */}
      <div style={{ display: "flex", gap: "var(--space-2)", alignItems: "flex-end" }}>
        <textarea
          ref={inputRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Reply to C-IAW, or type your preferences..."
          disabled={disabled}
          rows={2}
          style={{
            flex: 1,
            resize: "none",
            padding: "var(--space-3) var(--space-4)",
            background: "rgba(13,19,32,0.8)",
            border: "1px solid var(--color-border)",
            borderRadius: "var(--radius-md)",
            color: "var(--color-text-primary)",
            fontFamily: "var(--font-sans)",
            fontSize: "0.875rem",
            lineHeight: 1.5,
            outline: "none",
            transition: "border-color var(--transition-fast)",
          }}
          onFocus={(e) => e.target.style.borderColor = "var(--color-primary)"}
          onBlur={(e) => e.target.style.borderColor = "var(--color-border)"}
        />
        {/* Send button */}
        <button
          onClick={handleSend}
          disabled={!text.trim() || disabled}
          style={{
            padding: "var(--space-3) var(--space-4)",
            background: text.trim() && !disabled
              ? "linear-gradient(135deg,#3b82f6,#8b5cf6)"
              : "rgba(59,130,246,0.15)",
            border: "none", borderRadius: "var(--radius-md)",
            color: text.trim() && !disabled ? "#fff" : "var(--color-text-muted)",
            cursor: text.trim() && !disabled ? "pointer" : "not-allowed",
            fontSize: "1.1rem",
            transition: "all var(--transition-fast)",
            alignSelf: "stretch", display: "flex", alignItems: "center",
          }}
          title="Send message"
        >
          ➤
        </button>
      </div>

      {/* Job Hunt button */}
      <button
        onClick={handleJobSearch}
        disabled={searching || disabled}
        style={{
          width: "100%",
          padding: "var(--space-2) var(--space-4)",
          background: "linear-gradient(135deg, rgba(59,130,246,0.15), rgba(139,92,246,0.15))",
          border: "1px solid rgba(99,179,237,0.2)",
          borderRadius: "var(--radius-md)",
          color: searching || disabled ? "var(--color-text-muted)" : "var(--color-text-accent)",
          cursor: searching || disabled ? "not-allowed" : "pointer",
          fontSize: "0.8rem", fontWeight: 600,
          display: "flex", alignItems: "center", justifyContent: "center", gap: "var(--space-2)",
          transition: "all var(--transition-fast)",
          fontFamily: "var(--font-sans)",
        }}
        onMouseEnter={(e) => !searching && !disabled && (e.target.style.borderColor = "rgba(99,179,237,0.5)")}
        onMouseLeave={(e) => e.target.style.borderColor = "rgba(99,179,237,0.2)"}
        title="Start autonomous job search"
      >
        {searching ? <Spinner size={14} /> : <span>🔍</span>}
        {searching ? "Hunting jobs..." : "Start Job Hunt"}
      </button>
    </div>
  );
}
