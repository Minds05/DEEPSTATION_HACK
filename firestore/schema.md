# Firestore Schema — C-IAW Agent

## Access Pattern
- **Backend (Admin SDK)**: Full trust — bypasses all security rules.
- **Frontend (Client SDK)**: Rules-enforced — owner-only access.
- **PII (email, phone)**: Written only via Admin SDK. Never exposed in chat/thought logs.

---

## Collections

### `users/{userId}/profile`
Core resume-derived user profile. Populated by `resume_parser.py` after PDF upload.

| Field | Type | Notes |
|---|---|---|
| `name` | string | Full name |
| `email` | string | **PII — Admin SDK write only** |
| `phone` | string | **PII — Admin SDK write only** |
| `linkedin_url` | string | Profile URL |
| `skills` | array<string> | Extracted technical skills |
| `seniority` | string | e.g. "Senior", "Mid", "Junior" |
| `years_experience` | number | Total YoE |
| `projects` | array<object> | `{title, description, impact, technologies[]}` |
| `education` | array<object> | `{degree, institution, year}` |
| `resume_url` | string | Firebase Storage path |
| `parsed_at` | timestamp | Last parse timestamp |

---

### `users/{userId}/preferences`
User's job search preferences set during the interactive audit (Zone A chat).

| Field | Type | Notes |
|---|---|---|
| `location` | string | e.g. "Bangalore", "Remote" |
| `role_type` | string | e.g. "AIML Engineer", "Backend SWE" |
| `remote_only` | boolean | |
| `target_companies` | array<string> | Preferred companies |
| `exclude_companies` | array<string> | Blocklist |
| `updated_at` | timestamp | |

---

### `users/{userId}/task_status`
Orchestrator heartbeat. Updated on every state transition by `orchestrator.py`.

| Field | Type | Notes |
|---|---|---|
| `agent` | string | Always `"Career_Worker"` |
| `last_action` | string | e.g. `"Auto_Apply"`, `"Job_Search"` |
| `target` | string | Company name |
| `score` | number | Match score (0–100) |
| `status` | string | `Running \| Success \| Failed \| Paused \| Idle` |
| `updated_at` | timestamp | |

---

### `job_pool/{jobId}`
All jobs discovered by the hunt phase. Populates Zone C job cards.

| Field | Type | Notes |
|---|---|---|
| `title` | string | Job title |
| `company` | string | Company name |
| `url` | string | Direct application URL |
| `ats_type` | string | `lever \| greenhouse \| workday \| other` |
| `match_score` | number | 0–100 from scorer.py |
| `decision` | string | `AUTO_APPLY \| MANUAL_REQUIRED \| RECOMMENDATION` |
| `description_raw` | string | Full JD text |
| `vector_score` | number | 40% component |
| `reasoning_score` | number | 60% component |
| `reasoning_summary` | string | Gemini explanation |
| `discovered_at` | timestamp | |
| `userId` | string | Owner reference |

---

### `applications/{appId}`
Application execution records. One document per submitted/attempted application.

| Field | Type | Notes |
|---|---|---|
| `jobId` | string | Reference to `job_pool/{jobId}` |
| `userId` | string | Owner |
| `status` | string | `Pending \| Applied \| Manual_Required \| Failed \| manual_intervention_required` |
| `match_score` | number | Final score at time of application |
| `cover_letter` | string | Generated cover letter (Workday only) |
| `cover_letter_url` | string | Firebase Storage path to PDF |
| `screenshot_url` | string | Firebase Storage path to confirmation PNG |
| `timestamp` | timestamp | Submission time |
| `error_log` | string | Captcha/ATS block reason |
| `ats_type` | string | ATS at time of submission |

---

### `thought_logs/{logId}`
Streamed orchestrator thought log entries. Powers Zone B Activity Feed.

| Field | Type | Notes |
|---|---|---|
| `userId` | string | Owner |
| `type` | string | `Thought \| Action \| Warning \| Error \| Success` |
| `message` | string | Log entry — **NO PII allowed** |
| `timestamp` | timestamp | |
| `job_id` | string | (optional) related job |
| `app_id` | string | (optional) related application |

---

## Firebase Storage Paths

```
gs://{bucket}/
├── resumes/{userId}/{filename}.pdf          → Uploaded resume
├── screenshots/{userId}/{appId}.png         → Auto-apply confirmation
└── covers/{userId}/{appId}.pdf              → Generated cover letters
```
