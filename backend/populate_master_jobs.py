"""
populate_master_jobs.py — One-time seed of the master job database.
Run ONCE to populate the master_jobs collection in Firestore.

    python populate_master_jobs.py

This is the "job board" — jobs are matched against the user's resume
by the backend, NOT shown directly in Zone C.
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
COLLECTION = "master_jobs"
NOW = datetime.now(timezone.utc)

MASTER_JOBS = [
    {
        "title": "Senior ML Engineer",
        "company": "DeepMind",
        "url": "https://boards.greenhouse.io/deepmind/jobs/001",
        "atsType": "GREENHOUSE",
        "requiredSkills": ["Python", "PyTorch", "TensorFlow", "Distributed Training", "GCP", "CUDA", "Kubernetes"],
        "seniority": "Senior",
        "descriptionRaw": "Design and train large-scale foundation models. Lead ML infrastructure on GCP with PyTorch and distributed GPU clusters.",
    },
    {
        "title": "AI Research Engineer",
        "company": "Google Brain",
        "url": "https://boards.greenhouse.io/googlebrain/jobs/002",
        "atsType": "GREENHOUSE",
        "requiredSkills": ["Python", "JAX", "TensorFlow", "Research", "NLP", "Computer Vision", "Machine Learning"],
        "seniority": "Senior",
        "descriptionRaw": "Push state-of-the-art generative model research. Publish papers and implement novel architectures.",
    },
    {
        "title": "Full-Stack AI Engineer",
        "company": "Anthropic",
        "url": "https://boards.greenhouse.io/anthropic/jobs/003",
        "atsType": "GREENHOUSE",
        "requiredSkills": ["Python", "React", "FastAPI", "LLM", "REST API", "TypeScript", "Docker"],
        "seniority": "Mid",
        "descriptionRaw": "Build Claude-powered applications. Full stack development with LLM API integrations and React frontends.",
    },
    {
        "title": "MLOps Engineer",
        "company": "Cohere",
        "url": "https://boards.greenhouse.io/cohere/jobs/004",
        "atsType": "GREENHOUSE",
        "requiredSkills": ["Python", "Kubernetes", "Airflow", "Docker", "GCP", "MLflow", "CI/CD"],
        "seniority": "Mid",
        "descriptionRaw": "Scale enterprise AI inference infrastructure. Build model serving pipelines with Kubernetes and Airflow.",
    },
    {
        "title": "Lead AI Engineer",
        "company": "Microsoft Research",
        "url": "https://jobs.lever.co/microsoft/005",
        "atsType": "LEVER",
        "requiredSkills": ["Python", "Azure", "Machine Learning", "Team Leadership", "LLM", "Research", "C++"],
        "seniority": "Lead",
        "descriptionRaw": "Lead a team of AI engineers working on Foundation Models and AI Safety at Microsoft Research.",
    },
    {
        "title": "Principal Data Scientist",
        "company": "Meta AI",
        "url": "https://metacareers.com/jobs/006",
        "atsType": "WORKDAY",
        "requiredSkills": ["Python", "Spark", "SQL", "Machine Learning", "Recommendation Systems", "A/B Testing", "Scala"],
        "seniority": "Principal",
        "descriptionRaw": "Improve content ranking and feed algorithms. Work on large-scale recommendation systems for billions of users.",
    },
    {
        "title": "AI Platform Engineer",
        "company": "OpenAI",
        "url": "https://jobs.lever.co/openai/007",
        "atsType": "LEVER",
        "requiredSkills": ["Python", "API Design", "FastAPI", "Distributed Systems", "Go", "Kubernetes", "PostgreSQL"],
        "seniority": "Senior",
        "descriptionRaw": "Build the platform supporting millions of API users. Design scalable developer tooling for AI APIs.",
    },
    {
        "title": "Machine Learning Engineer",
        "company": "Hugging Face",
        "url": "https://apply.workable.com/huggingface/j/008",
        "atsType": "UNKNOWN",
        "requiredSkills": ["Python", "PyTorch", "NLP", "Transformers", "Rust", "Open Source", "HuggingFace"],
        "seniority": "Mid",
        "descriptionRaw": "Improve the Transformers library and model hub. Contribute to open-source AI tooling.",
    },
    {
        "title": "Backend Engineer (AI Infra)",
        "company": "Mistral AI",
        "url": "https://mistral.ai/careers/009",
        "atsType": "WORKDAY",
        "requiredSkills": ["Python", "FastAPI", "gRPC", "Distributed Systems", "C++", "Linux", "Optimization"],
        "seniority": "Senior",
        "descriptionRaw": "Build high-throughput inference servers for Mistral models. Optimize model serving latency at scale.",
    },
    {
        "title": "Data Engineer",
        "company": "Databricks",
        "url": "https://databricks.com/careers/010",
        "atsType": "UNKNOWN",
        "requiredSkills": ["Python", "Spark", "Kafka", "SQL", "Delta Lake", "Airflow", "Scala"],
        "seniority": "Mid",
        "descriptionRaw": "Build scalable ETL pipelines on the Lakehouse platform. Work with Spark and Kafka at massive scale.",
    },
    {
        "title": "Research Scientist (NLP)",
        "company": "AI21 Labs",
        "url": "https://ai21.com/careers/011",
        "atsType": "UNKNOWN",
        "requiredSkills": ["Python", "NLP", "PyTorch", "Research", "Deep Learning", "Machine Learning", "PhD"],
        "seniority": "Senior",
        "descriptionRaw": "Advance Jurassic model capabilities in NLP. Publish research and implement novel architectures.",
    },
    {
        "title": "Cloud AI Architect",
        "company": "AWS",
        "url": "https://aws.amazon.com/careers/012",
        "atsType": "UNKNOWN",
        "requiredSkills": ["AWS", "SageMaker", "Machine Learning", "Architecture", "Python", "Cloud", "Terraform"],
        "seniority": "Senior",
        "descriptionRaw": "Design enterprise ML solutions on AWS. Help customers architect AI workloads on SageMaker.",
    },
    {
        "title": "Computer Vision Engineer",
        "company": "Tesla",
        "url": "https://tesla.com/careers/013",
        "atsType": "WORKDAY",
        "requiredSkills": ["Python", "Computer Vision", "PyTorch", "C++", "CUDA", "OpenCV", "Deep Learning"],
        "seniority": "Mid",
        "descriptionRaw": "Build perception systems for Autopilot. Train and optimize real-time CV models for self-driving.",
    },
    {
        "title": "Generative AI Engineer",
        "company": "Adobe",
        "url": "https://adobe.com/careers/014",
        "atsType": "WORKDAY",
        "requiredSkills": ["Python", "Diffusion Models", "PyTorch", "Generative AI", "React", "API Design", "ML"],
        "seniority": "Mid",
        "descriptionRaw": "Integrate Firefly AI into creative products. Build generative image and video APIs for millions of creators.",
    },
    {
        "title": "AI Safety Researcher",
        "company": "Redwood Research",
        "url": "https://redwoodresearch.org/careers/015",
        "atsType": "GREENHOUSE",
        "requiredSkills": ["Python", "Machine Learning", "Research", "PyTorch", "NLP", "RLHF", "Alignment"],
        "seniority": "Senior",
        "descriptionRaw": "Work on interpretability and AI alignment problems. Design experiments to understand and constrain model behavior.",
    },
]

# Clear existing master_jobs first (clean slate)
existing = db.collection(COLLECTION).stream()
deleted = 0
for doc in existing:
    doc.reference.delete()
    deleted += 1
if deleted:
    print(f"Cleared {deleted} existing master_jobs.")

print(f"\nSeeding {len(MASTER_JOBS)} master jobs...")
for job in MASTER_JOBS:
    job_id = str(uuid.uuid4())
    # Provide default location and package if not explicitly in the dict
    loc = job.get("location", "San Francisco, CA")
    pkg = job.get("package", "$150k - $250k")
    db.collection(COLLECTION).document(job_id).set({
        "jobId": job_id,
        "title": job["title"],
        "company": job["company"],
        "url": job["url"],
        "atsType": job["atsType"],
        "requiredSkills": job["requiredSkills"],
        "seniority": job["seniority"],
        "descriptionRaw": job["descriptionRaw"],
        "location": loc,
        "package": pkg,
        "createdAt": NOW,
    })
    print(f"  [OK] {job['title']} @ {job['company']}")

print(f"\nDone! {len(MASTER_JOBS)} jobs in '{COLLECTION}' collection.")
print("These will be matched against each user's resume after parse.")
