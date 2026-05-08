import { useEffect } from "react";
import ZoneA from "./ZoneA";
import ZoneB from "./ZoneB";
import ZoneC from "./ZoneC";
import {
  useJobsListener,
  useThoughtLogsListener,
  useTaskStatusListener,
  useApplicationsListener,
} from "../../hooks/useFirestore";

/**
 * AppShell — Three-zone grid layout root
 * Mounts all Firestore real-time listeners.
 * Renders the three zones in a 28/44/28 column layout.
 */
export default function AppShell() {
  // Mount real-time Firestore listeners for all zones
  useJobsListener();
  useThoughtLogsListener();
  useTaskStatusListener();
  useApplicationsListener();


  return (
    <div className="app-shell">
      <ZoneA />
      <ZoneB />
      <ZoneC />
    </div>
  );
}
