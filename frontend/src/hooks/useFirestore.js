/**
 * useFirestore — Real-time Firestore listeners for Zone C and Zone B
 *
 * Firestore composite indexes required for compound queries.
 * To avoid index errors while indexes are being built, we:
 *  - Query with only `where` (no compound orderBy) from Firestore
 *  - Sort client-side in JS after data arrives
 *
 * To create the indexes properly, run:
 *   firebase deploy --only firestore:indexes
 * (firestore.indexes.json is in the firestore/ directory)
 */
import { useEffect } from "react";
import {
  collection,
  query,
  where,
  limit,
  onSnapshot,
  doc,
} from "firebase/firestore";
import { db } from "../services/firebase";
import useAgentStore from "../store/agentStore";

const USER_ID = import.meta.env.VITE_USER_ID || "local_user";


/**
 * Subscribe to real-time job_pool updates → Zone C
 * Client-side sort by matchScore desc avoids composite index requirement.
 */
export function useJobsListener(maxJobs = 50) {
  const setJobs = useAgentStore((s) => s.setJobs);

  useEffect(() => {
    // Simple single-field where — no orderBy → no composite index needed
    const q = query(
      collection(db, "job_pool"),
      where("userId", "==", USER_ID),
      limit(maxJobs)
    );

    const unsub = onSnapshot(
      q,
      (snapshot) => {
        const jobs = snapshot.docs.map((d) => ({ jobId: d.id, ...d.data() }));
        // Client-side sort: highest matchScore first
        jobs.sort((a, b) => (b.matchScore ?? 0) - (a.matchScore ?? 0));
        setJobs(jobs);
      },
      (err) => console.error("[useJobsListener]", err.message)
    );

    return unsub;
  }, [setJobs, maxJobs]);
}


/**
 * Subscribe to real-time thought_logs updates → Zone B
 * ONLY shows logs from the current session (created after page load).
 * Previous session logs are ignored to keep the feed clean.
 */
export function useThoughtLogsListener(maxLogs = 100) {
  const addThoughtLog = useAgentStore((s) => s.addThoughtLog);

  useEffect(() => {
    // Capture session start time — only show logs created from this moment
    const sessionStart = new Date();

    const q = query(
      collection(db, "thought_logs"),
      where("userId", "==", USER_ID),
      limit(maxLogs)
    );

    const seenIds = new Set();

    const unsub = onSnapshot(
      q,
      (snapshot) => {
        snapshot.docChanges().forEach((change) => {
          if (change.type === "added" && !seenIds.has(change.doc.id)) {
            const data = change.doc.data();
            
            // Client-side filter for current session only
            // Fallback to 0 if missing so we don't crash
            const logTime = data.timestamp?.toMillis?.() || 0;
            if (logTime >= sessionStart.getTime()) {
              seenIds.add(change.doc.id);
              addThoughtLog({ logId: change.doc.id, ...data });
            }
          }
        });
      },
      (err) => console.error("[useThoughtLogsListener]", err.message)
    );

    return unsub;
  }, [addThoughtLog]);
}




/**
 * Subscribe to orchestrator task_status → global status bar
 */
export function useTaskStatusListener() {
  const setTaskStatus = useAgentStore((s) => s.setTaskStatus);

  useEffect(() => {
    const docRef = doc(
      db,
      "users", USER_ID,
      "task_status", "current"
    );

    const unsub = onSnapshot(
      docRef,
      (snap) => {
        if (snap.exists()) setTaskStatus(snap.data());
      },
      (err) => console.error("[useTaskStatusListener]", err.message)
    );

    return unsub;
  }, [setTaskStatus]);
}


/**
 * Subscribe to real-time applications updates → Applied Jobs tab
 * Sorted client-side by appliedAt descending.
 */
export function useApplicationsListener(maxApps = 100) {
  const setApplications = useAgentStore((s) => s.setApplications);

  useEffect(() => {
    const q = query(
      collection(db, "applications"),
      where("userId", "==", USER_ID),
      limit(maxApps)
    );

    const unsub = onSnapshot(
      q,
      (snapshot) => {
        const apps = snapshot.docs.map((d) => ({ appId: d.id, ...d.data() }));
        // Client-side sort: most recently applied first
        apps.sort((a, b) => {
          const ta = a.appliedAt?.toMillis?.() ?? 0;
          const tb = b.appliedAt?.toMillis?.() ?? 0;
          return tb - ta;
        });
        setApplications(apps);
      },
      (err) => console.error("[useApplicationsListener]", err.message)
    );

    return unsub;
  }, [setApplications, maxApps]);
}

