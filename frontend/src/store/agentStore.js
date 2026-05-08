// Zustand global state store for the C-IAW agent
import { create } from "zustand";

const useAgentStore = create((set, get) => ({
  // ── Agent / Orchestrator ─────────────────────────────────────
  taskStatus: {
    agent: "Career_Worker",
    last_action: "Idle",
    status: "Idle",
    target: null,
    score: null,
  },
  setTaskStatus: (status) => set({ taskStatus: status }),

  // ── Thought Logs (Zone B) ────────────────────────────────────
  thoughtLogs: [],
  addThoughtLog: (log) =>
    set((state) => ({ thoughtLogs: [log, ...state.thoughtLogs].slice(0, 200) })),
  clearThoughtLogs: () => set({ thoughtLogs: [] }),

  // ── Jobs (Zone C) ────────────────────────────────────────────
  jobs: [],
  setJobs: (jobs) => set({ jobs }),
  addJob: (job) =>
    set((state) => ({
      jobs: state.jobs.find((j) => j.job_id === job.job_id)
        ? state.jobs.map((j) => (j.job_id === job.job_id ? job : j))
        : [job, ...state.jobs],
    })),

  // ── Chat Messages (Zone A) ───────────────────────────────────
  messages: [],
  addMessage: (msg) =>
    set((state) => ({ messages: [...state.messages, msg] })),
  clearMessages: () => set({ messages: [] }),

  // ── Resume State ─────────────────────────────────────────────
  resumeUploaded: false,
  userProfile: null,
  setResumeUploaded: (val) => set({ resumeUploaded: val }),
  setUserProfile: (profile) => set({ userProfile: profile }),

  // ── Applications ─────────────────────────────────────────────
  applications: [],
  setApplications: (apps) => set({ applications: apps }),
  addApplication: (app) =>
    set((state) => ({
      applications: [app, ...state.applications],
    })),

  // ── Cover Letter Modal ────────────────────────────────────────
  coverLetterModal: {
    open: false,
    jobId: null,
    jobTitle: null,
    jobCompany: null,
    text: null,
    url: null,
    loading: false,
    error: null,
  },
  openCoverLetterModal: (job) =>
    set({ coverLetterModal: { open: true, jobId: job.jobId, jobTitle: job.title,
      jobCompany: job.company, text: job.coverLetterText || null,
      url: job.coverLetterUrl || null, loading: false, error: null } }),
  closeCoverLetterModal: () =>
    set((s) => ({ coverLetterModal: { ...s.coverLetterModal, open: false } })),
  setCoverLetterResult: (text, url) =>
    set((s) => ({ coverLetterModal: { ...s.coverLetterModal, text, url, loading: false, error: null } })),
  setCoverLetterLoading: (loading) =>
    set((s) => ({ coverLetterModal: { ...s.coverLetterModal, loading } })),
  setCoverLetterError: (error) =>
    set((s) => ({ coverLetterModal: { ...s.coverLetterModal, error, loading: false } })),
}));

export default useAgentStore;
