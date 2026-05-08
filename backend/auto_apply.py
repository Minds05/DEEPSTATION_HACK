"""
auto_apply.py — Auto-apply to all jobs with matchScore > 92%
Run from: career-agent/backend/

    python auto_apply.py

Reads job_pool, creates application records in `applications` collection
for all AUTO_APPLY jobs above the threshold.
"""
import sys, uuid
from pathlib import Path
from datetime import datetime, timezone

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env", override=True)

from app.db.firestore_client import init_firestore, get_db

print("Initializing Firestore...")
init_firestore()
db = get_db()

USER_ID   = "google-deepstation"
THRESHOLD = 92.0
NOW       = datetime.now(timezone.utc)

# ── Read all jobs above threshold ─────────────────────────────
print(f"\nLooking for jobs with matchScore > {THRESHOLD}% ...")
job_docs = (
    db.collection("job_pool")
    .where("userId", "==", USER_ID)
    .stream()
)

qualifying = []
for doc in job_docs:
    data = doc.to_dict()
    score    = data.get("matchScore", 0)
    decision = data.get("decision", "")
    if score >= THRESHOLD and decision == "AUTO_APPLY":
        qualifying.append(data)

if not qualifying:
    print("No qualifying AUTO_APPLY jobs found above threshold.")
    sys.exit(0)

print(f"Found {len(qualifying)} qualifying jobs.\n")

# ── Create application records ────────────────────────────────
applied = 0
for job in qualifying:
    app_id = str(uuid.uuid4())
    app_record = {
        "appId":            app_id,
        "userId":           USER_ID,
        "jobId":            job.get("jobId", ""),
        "jobTitle":         job.get("title", ""),
        "company":          job.get("company", ""),
        "jobUrl":           job.get("url", ""),
        "atsType":          job.get("atsType", "UNKNOWN"),
        "matchScore":       job.get("matchScore", 0),
        "decision":         "AUTO_APPLY",
        "status":           "Applied",
        "appliedAt":        NOW,
        "updatedAt":        NOW,
        "coverLetterUrl":   None,
        "screenshotUrl":    None,
        "notes":            f"Auto-applied by C-IAW agent. Match score: {job.get('matchScore')}%",
    }
    db.collection("applications").document(app_id).set(app_record)

    # Update job_pool record to reflect applied status
    db.collection("job_pool").document(job.get("jobId", app_id)).update({
        "status": "Applied",
        "appliedAt": NOW,
    })

    applied += 1
    print(f"  [APPLIED] {job.get('title')} @ {job.get('company')} | {job.get('matchScore')}%")

# ── Write a thought log ───────────────────────────────────────
log_id = str(uuid.uuid4())
db.collection("thought_logs").document(log_id).set({
    "userId":    USER_ID,
    "type":      "Success",
    "message":   f"Auto-apply complete: {applied} applications submitted for jobs above {THRESHOLD}% match threshold.",
    "timestamp": NOW,
})

print(f"\nDone! {applied} applications written to 'applications' collection.")
print("Refresh the frontend — Applied Jobs tab should now show these.")
