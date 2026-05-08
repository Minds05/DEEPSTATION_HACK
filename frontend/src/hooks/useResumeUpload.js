/**
 * useResumeUpload — Custom hook for PDF upload + parse flow
 *
 * Manages the full two-step resume ingestion:
 * 1. POST /resume/upload  → Firebase Storage
 * 2. POST /resume/parse   → Gemini → Firestore profile
 *
 * Updates Zustand store with profile and audit message on success.
 */
import { useState, useCallback } from "react";
import api from "../services/api";
import useAgentStore from "../store/agentStore";

export function useResumeUpload() {
  const [uploadState, setUploadState] = useState("idle"); // idle | uploading | parsing | done | error
  const [error, setError] = useState(null);
  const [resumeUrl, setResumeUrl] = useState(null);

  const { setResumeUploaded, setUserProfile, addMessage, addThoughtLog } =
    useAgentStore();

  const uploadAndParse = useCallback(async (file) => {
    if (!file || file.type !== "application/pdf") {
      setError("Only PDF files are accepted.");
      return;
    }

    setError(null);

    // ── Step 1: Upload to Firebase Storage ─────────────────────
    setUploadState("uploading");
    addThoughtLog({
      type: "Thought",
      message: `Uploading resume: ${file.name}`,
      timestamp: new Date().toISOString(),
    });

    let uploadData;
    try {
      const formData = new FormData();
      formData.append("file", file);

      const uploadRes = await api.post("/resume/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      uploadData = uploadRes.data;
      setResumeUrl(uploadData.resume_url);

      addThoughtLog({
        type: "Action",
        message: `Resume stored in Firebase Storage.`,
        timestamp: new Date().toISOString(),
      });
    } catch (err) {
      const msg = err?.response?.data?.detail || "Upload failed.";
      setError(msg);
      setUploadState("error");
      addThoughtLog({
        type: "Error",
        message: `Upload failed: ${msg}`,
        timestamp: new Date().toISOString(),
      });
      return;
    }

    // ── Step 2: Gemini Parse → Firestore ───────────────────────
    setUploadState("parsing");
    addThoughtLog({
      type: "Thought",
      message: "Sending resume to Gemini 2.0 Flash for analysis...",
      timestamp: new Date().toISOString(),
    });

    try {
      const parseRes = await api.post("/resume/parse");
      const { profile, audit_message } = parseRes.data;

      setUserProfile(profile);
      setResumeUploaded(true);
      setUploadState("done");

      // Add Zone A audit message to chat
      addMessage({
        id: Date.now(),
        role: "agent",
        content: audit_message,
        timestamp: new Date().toISOString(),
      });

      addThoughtLog({
        type: "Success",
        message: `Resume analysis complete. Found ${profile.skills?.length || 0} skills. Seniority: ${profile.seniority}.`,
        timestamp: new Date().toISOString(),
      });
    } catch (err) {
      const msg = err?.response?.data?.detail || "Gemini parsing failed.";
      setError(msg);
      setUploadState("error");
      addThoughtLog({
        type: "Error",
        message: `Parsing failed: ${msg}`,
        timestamp: new Date().toISOString(),
      });
    }
  }, [addMessage, addThoughtLog, setResumeUploaded, setUserProfile]);

  const reset = useCallback(() => {
    setUploadState("idle");
    setError(null);
    setResumeUrl(null);
  }, []);

  return { uploadState, error, resumeUrl, uploadAndParse, reset };
}
