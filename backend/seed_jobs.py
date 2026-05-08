"""
seed_jobs.py — Populate Firestore job_pool with realistic dummy data.
Run from: career-agent/backend/

    python seed_jobs.py

Creates 12 jobs across all 3 decision types for user: google-deepstation
"""
import sys, uuid
from pathlib import Path
from datetime import datetime, timezone

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env", override=True)

# ── Bootstrap app context ─────────────────────────────────────
from app.db.firestore_client import init_firestore
from app.db.firestore_client import get_db

print("Initializing Firestore...")
init_firestore()
db = get_db()

USER_ID    = "google-deepstation"
COLLECTION = "job_pool"

NOW = datetime.now(timezone.utc)

# ── Dummy jobs ────────────────────────────────────────────────
JOBS = [
    # ── AUTO_APPLY — Greenhouse ATS (high scores) ─────────────
    {
        "title": "Senior ML Engineer",
        "company": "DeepMind",
        "url": "https://boards.greenhouse.io/deepmind/jobs/12345",
        "atsType": "GREENHOUSE",
        "matchScore": 96.4,
        "vectorScore": 95.1,
        "reasoningScore": 97.7,
        "decision": "AUTO_APPLY",
        "reasoningSummary": "Exceptional alignment: Python, PyTorch, distributed training, and GCP match 9/10 required skills. Seniority matches perfectly.",
        "descriptionRaw": "We are looking for a Senior ML Engineer to join our team to work on large-scale model training infrastructure...",
    },
    {
        "title": "AI Research Engineer",
        "company": "Google Brain",
        "url": "https://boards.greenhouse.io/googlebrain/jobs/67890",
        "atsType": "GREENHOUSE",
        "matchScore": 94.1,
        "vectorScore": 93.8,
        "reasoningScore": 94.4,
        "decision": "AUTO_APPLY",
        "reasoningSummary": "Strong match on transformer research, JAX, and publication record. Location flexible.",
        "descriptionRaw": "Google Brain is seeking an AI Research Engineer to push state-of-the-art in generative models...",
    },
    {
        "title": "Full-Stack AI Engineer",
        "company": "Anthropic",
        "url": "https://boards.greenhouse.io/anthropic/jobs/11223",
        "atsType": "GREENHOUSE",
        "matchScore": 93.5,
        "vectorScore": 92.0,
        "reasoningScore": 95.0,
        "decision": "AUTO_APPLY",
        "reasoningSummary": "React + FastAPI + LLM integration — exact match. Strong culture fit signals.",
        "descriptionRaw": "Join Anthropic to build Claude-powered applications. Full stack role with LLM API integrations...",
    },
    {
        "title": "MLOps Engineer",
        "company": "Cohere",
        "url": "https://boards.greenhouse.io/cohere/jobs/99887",
        "atsType": "GREENHOUSE",
        "matchScore": 92.2,
        "vectorScore": 91.5,
        "reasoningScore": 92.9,
        "decision": "AUTO_APPLY",
        "reasoningSummary": "Kubernetes, Airflow, model serving pipeline — high overlap with candidate's DevOps background.",
        "descriptionRaw": "Cohere needs an MLOps Engineer to scale our enterprise AI inference infrastructure...",
    },

    # ── MANUAL_REQUIRED — Workday/Lever (complex ATS) ─────────
    {
        "title": "Lead AI Engineer",
        "company": "Microsoft Research",
        "url": "https://jobs.lever.co/microsoft/aaa-111",
        "atsType": "LEVER",
        "matchScore": 95.3,
        "vectorScore": 94.0,
        "reasoningScore": 96.6,
        "decision": "MANUAL_REQUIRED",
        "reasoningSummary": "Perfect seniority and skills match but Lever ATS requires custom cover letter and portfolio links.",
        "descriptionRaw": "Microsoft Research is hiring a Lead AI Engineer to work on Foundation Models and AI Safety...",
    },
    {
        "title": "Principal Data Scientist",
        "company": "Meta AI",
        "url": "https://metacareers.com/jobs/workday/555666",
        "atsType": "WORKDAY",
        "matchScore": 93.8,
        "vectorScore": 92.5,
        "reasoningScore": 95.1,
        "decision": "MANUAL_REQUIRED",
        "reasoningSummary": "Excellent fit for recommendation systems role. Workday ATS needs manual application with video intro.",
        "descriptionRaw": "Meta AI is seeking a Principal Data Scientist to improve content ranking and feed algorithms...",
    },
    {
        "title": "AI Platform Engineer",
        "company": "OpenAI",
        "url": "https://jobs.lever.co/openai/bbb-222",
        "atsType": "LEVER",
        "matchScore": 92.7,
        "vectorScore": 91.8,
        "reasoningScore": 93.6,
        "decision": "MANUAL_REQUIRED",
        "reasoningSummary": "Strong alignment with API platform and developer tooling experience. Lever requires custom answers.",
        "descriptionRaw": "OpenAI is growing its platform team to support millions of API users worldwide...",
    },
    {
        "title": "Senior Backend Engineer (AI Infra)",
        "company": "Mistral AI",
        "url": "https://mistral.ai/careers/workday/333444",
        "atsType": "WORKDAY",
        "matchScore": 92.0,
        "vectorScore": 90.5,
        "reasoningScore": 93.5,
        "decision": "MANUAL_REQUIRED",
        "reasoningSummary": "FastAPI + gRPC + distributed systems — great overlap. Workday ATS requires manual form completion.",
        "descriptionRaw": "Mistral AI needs a Senior Backend Engineer to build high-throughput inference servers...",
    },

    # ── RECOMMENDATION — Strong but below AUTO_APPLY threshold ─
    {
        "title": "Machine Learning Engineer",
        "company": "Hugging Face",
        "url": "https://apply.workable.com/huggingface/j/ABC123",
        "atsType": "UNKNOWN",
        "matchScore": 87.5,
        "vectorScore": 86.0,
        "reasoningScore": 89.0,
        "decision": "RECOMMENDATION",
        "reasoningSummary": "Good skills overlap but role needs Rust experience which is absent in profile.",
        "descriptionRaw": "Hugging Face is looking for ML Engineers to improve the Transformers library and model hub...",
    },
    {
        "title": "Data Engineer",
        "company": "Databricks",
        "url": "https://databricks.com/company/careers/all-department/job/111222",
        "atsType": "UNKNOWN",
        "matchScore": 85.2,
        "vectorScore": 84.0,
        "reasoningScore": 86.4,
        "decision": "RECOMMENDATION",
        "reasoningSummary": "Spark and Kafka skills match, but role skews more toward data engineering than AI/ML.",
        "descriptionRaw": "Databricks seeks a Data Engineer to build scalable ETL pipelines on the Lakehouse platform...",
    },
    {
        "title": "Research Scientist (NLP)",
        "company": "AI21 Labs",
        "url": "https://ai21.com/careers/nlp-scientist",
        "atsType": "UNKNOWN",
        "matchScore": 84.0,
        "vectorScore": 83.0,
        "reasoningScore": 85.0,
        "decision": "RECOMMENDATION",
        "reasoningSummary": "Strong NLP background but requires PhD. Consider applying if willing to discuss compensation.",
        "descriptionRaw": "AI21 Labs is looking for NLP Research Scientists to advance Jurassic model capabilities...",
    },
    {
        "title": "Cloud AI Architect",
        "company": "AWS",
        "url": "https://aws.amazon.com/careers/cloud-ai-architect",
        "atsType": "UNKNOWN",
        "matchScore": 82.5,
        "vectorScore": 81.0,
        "reasoningScore": 84.0,
        "decision": "RECOMMENDATION",
        "reasoningSummary": "AWS certifications missing but cloud ML deployment experience compensates partially.",
        "descriptionRaw": "Amazon Web Services needs a Cloud AI Architect to design enterprise ML solutions on AWS...",
    },
]

# ── Write to Firestore ────────────────────────────────────────
print(f"\nSeeding {len(JOBS)} jobs for user: {USER_ID}\n")

counts = {"AUTO_APPLY": 0, "MANUAL_REQUIRED": 0, "RECOMMENDATION": 0}

for job in JOBS:
    job_id = str(uuid.uuid4())
    doc = {
        "jobId":            job_id,
        "userId":           USER_ID,
        "title":            job["title"],
        "company":          job["company"],
        "url":              job["url"],
        "atsType":          job["atsType"],
        "matchScore":       job["matchScore"],
        "vectorScore":      job["vectorScore"],
        "reasoningScore":   job["reasoningScore"],
        "decision":         job["decision"],
        "reasoningSummary": job["reasoningSummary"],
        "descriptionRaw":   job["descriptionRaw"],
        "discoveredAt":     NOW,
        "updatedAt":        NOW,
    }
    db.collection(COLLECTION).document(job_id).set(doc)
    counts[job["decision"]] += 1
    print(f"  [OK] [{job['decision'][:4]}] {job['title']} @ {job['company']} ({job['matchScore']}%)")

print(f"\nDone! Written to Firestore collection: '{COLLECTION}'")
print(f"  AUTO_APPLY:      {counts['AUTO_APPLY']} jobs")
print(f"  MANUAL_REQUIRED: {counts['MANUAL_REQUIRED']} jobs")
print(f"  RECOMMENDATION:  {counts['RECOMMENDATION']} jobs")
print(f"\nRefresh the frontend — Zone C should show all {len(JOBS)} jobs.")
