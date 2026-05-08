import { useRef, useEffect, useCallback } from "react";
import ChatBubble from "../chat/ChatBubble";
import ChatInput from "../chat/ChatInput";
import ResumeUploader from "../resume/ResumeUploader";
import useAgentStore from "../../store/agentStore";
import api from "../../services/api";

/**
 * Zone A — Dialogue Panel (left column)
 * - Resume upload when no profile yet
 * - Chat interface with C-IAW agent messages
 * - Job search trigger
 */
export default function ZoneA() {
  const messages       = useAgentStore((s) => s.messages);
  const addMessage     = useAgentStore((s) => s.addMessage);
  const resumeUploaded = useAgentStore((s) => s.resumeUploaded);
  const userProfile    = useAgentStore((s) => s.userProfile);
  const taskStatus     = useAgentStore((s) => s.taskStatus);
  const chatEndRef     = useRef(null);

  // Auto-scroll to latest message
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const welcomeSent = useRef(false);

  // Welcome message on first load — useRef guard prevents React 18 StrictMode double-add
  useEffect(() => {
    if (!welcomeSent.current && messages.length === 0) {
      welcomeSent.current = true;
      addMessage({
        id: "welcome-init",
        role: "agent",
        content: "Welcome to C-IAW — your Career Intelligence & Automation Worker.\n\nUpload your resume above and I'll map your profile, identify your strongest skills, and hunt for your perfect match.",
        timestamp: new Date().toISOString(),
      });
    }
  }, []); // eslint-disable-line

  const handleSend = useCallback(async (text) => {
    addMessage({ id: Date.now(), role: "user",  content: text, timestamp: new Date().toISOString() });
    
    try {
      const res = await api.post("/agent/chat", { message: text });
      addMessage({
        id: Date.now() + 1,
        role: "agent",
        content: res.data.reply,
        timestamp: new Date().toISOString(),
      });
    } catch (err) {
      addMessage({
        id: Date.now() + 1,
        role: "agent",
        content: "Sorry, I had trouble processing your preferences right now.",
        timestamp: new Date().toISOString(),
      });
    }
  }, [addMessage]);

  const handleJobSearch = useCallback(async () => {
    if (!resumeUploaded) {
      addMessage({
        id: Date.now(), role: "agent",
        content: "⚠️ Upload and parse your resume first before I can start hunting.",
        timestamp: new Date().toISOString(),
      });
      return;
    }

    const prefs = {};
    if (userProfile) prefs.role = null; // Let job_hunter infer

    addMessage({
      id: Date.now(), role: "agent",
      content: `🔍 Mission started. I'm hunting for the best ${userProfile?.seniority || ""} roles on Lever and Greenhouse. Watch Zone B for live updates.`,
      timestamp: new Date().toISOString(),
    });

    try {
      await api.post("/jobs/search", {
        user_id: import.meta.env.VITE_USER_ID || "local_user",
        ...prefs,
      });
    } catch (err) {
      addMessage({
        id: Date.now(), role: "agent",
        content: `❌ Search failed: ${err?.response?.data?.detail || "Unknown error"}`,
        timestamp: new Date().toISOString(),
      });
    }
  }, [resumeUploaded, userProfile, addMessage]);

  const isHunting = taskStatus?.status === "Running";

  return (
    <div className="zone-a glass">
      {/* Header */}
      <div className="zone-header">
        <h2>Dialogue</h2>
        <span className="zone-badge">Zone A</span>
      </div>

      {/* Resume uploader — shown until resume is parsed */}
      {!resumeUploaded && (
        <div style={{ padding: "var(--space-4)", borderBottom: "1px solid var(--color-border)" }}>
          <ResumeUploader />
        </div>
      )}

      {/* Profile chip — shown after parse */}
      {resumeUploaded && userProfile && (
        <div style={{
          padding: "var(--space-3) var(--space-5)",
          borderBottom: "1px solid var(--color-border)",
          display: "flex", alignItems: "center", gap: "var(--space-3)",
        }}>
          {/* Avatar */}
          <div style={{
            width: 34, height: 34, borderRadius: "50%", flexShrink: 0,
            background: "linear-gradient(135deg,#3b82f6,#8b5cf6)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontWeight: 800, fontSize: "0.85rem", color: "#fff",
          }}>
            {userProfile.name?.[0] || "U"}
          </div>
          <div style={{ minWidth: 0 }}>
            <p style={{ fontWeight: 700, fontSize: "0.8rem", color: "var(--color-text-primary)" }}>
              {userProfile.name}
            </p>
            <p style={{ fontSize: "0.7rem", color: "var(--color-text-muted)" }}>
              {userProfile.seniority} · {userProfile.skills?.slice(0, 3).join(", ")}
            </p>
          </div>
          <div style={{ marginLeft: "auto" }}>
            {isHunting && (
              <span style={{
                fontSize: "0.68rem", color: "#60a5fa", fontWeight: 600,
                animation: "statusPulse 1.5s ease-in-out infinite",
              }}>● Hunting...</span>
            )}
          </div>
        </div>
      )}

      {/* Chat messages */}
      <div className="chat-body">
        {messages.map((msg) => (
          <ChatBubble key={msg.id} message={msg} />
        ))}
        <div ref={chatEndRef} />
      </div>

      {/* Input */}
      <div className="chat-footer">
        <ChatInput
          onSend={handleSend}
          onJobSearch={handleJobSearch}
          disabled={isHunting}
        />
      </div>
    </div>
  );
}
