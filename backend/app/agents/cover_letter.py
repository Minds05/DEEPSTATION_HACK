"""
Cover Letter Agent — Gemini 2.0 Flash

Generates a tailored, professional cover letter for a given job listing.
Outputs:
  1. Plain text (for storage/display)
  2. PDF bytes (for Firebase Storage upload + Zone C download)
"""
import re
import io
from typing import Optional

import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.models.resume import ResumeProfile
from app.utils.logger import get_logger

logger = get_logger(__name__)
genai.configure(api_key=settings.gemini_api_key)

_COVER_LETTER_PROMPT = """
You are an expert career writer. Write a concise, high-impact cover letter for the job below.

Requirements:
- Max 3 paragraphs: (1) hook/fit, (2) top 2 relevant achievements with metrics, (3) call to action
- Professional but not generic — tie skills directly to the JD
- Do NOT repeat the resume verbatim; synthesize
- Do NOT include date, address blocks, or placeholders like [Company Name]
- Write in first person. Tone: confident, direct, enthusiastic
- Max 250 words

Candidate Profile:
- Name: {name}
- Seniority: {seniority} ({yoe} years experience)
- Top skills: {skills}
- Key projects:
{projects}

Job:
- Title: {title}
- Company: {company}
- Description:
{jd_text}

Return ONLY the cover letter text. No headers, no labels.
"""


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
async def generate_cover_letter(
    profile: ResumeProfile,
    job_title: str,
    job_company: str,
    jd_text: str,
) -> str:
    """
    Generate a tailored cover letter for a specific job.
    Returns raw cover letter text.
    """
    model = genai.GenerativeModel(settings.gemini_model)

    projects_text = "\n".join(
        f"  - {p.title}: {p.impact}" for p in profile.projects[:3]
    ) or "  - See resume for project details."

    prompt = _COVER_LETTER_PROMPT.format(
        name=profile.name,
        seniority=profile.seniority,
        yoe=profile.years_experience or "several",
        skills=", ".join(profile.skills[:8]),
        projects=projects_text,
        title=job_title,
        company=job_company,
        jd_text=jd_text[:2500],
    )

    response = await model.generate_content_async(
        prompt,
        generation_config={"temperature": 0.7, "max_output_tokens": 600},
    )
    text = response.text.strip()
    logger.info(f"Cover letter generated: {len(text)} chars for {job_title} @ {job_company}")
    return text


def generate_pdf(cover_letter_text: str, candidate_name: str, job_title: str, company: str) -> bytes:
    """
    Convert cover letter text to a PDF using reportlab.
    Returns raw PDF bytes.
    Falls back to plain text wrapped in a minimal PDF if reportlab unavailable.
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.enums import TA_LEFT

        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=letter,
            rightMargin=1 * inch, leftMargin=1 * inch,
            topMargin=1 * inch, bottomMargin=1 * inch,
        )
        styles = getSampleStyleSheet()
        normal = ParagraphStyle(
            "body",
            fontName="Helvetica",
            fontSize=11,
            leading=16,
            alignment=TA_LEFT,
        )
        heading = ParagraphStyle(
            "heading",
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=18,
            textColor=colors.HexColor("#1d4ed8"),
        )

        story = [
            Paragraph(candidate_name, heading),
            Spacer(1, 6),
            Paragraph(f"Application for: {job_title} — {company}", normal),
            Spacer(1, 20),
        ]

        # Split into paragraphs on double newlines
        for para in cover_letter_text.split("\n\n"):
            para = para.strip()
            if para:
                story.append(Paragraph(para.replace("\n", " "), normal))
                story.append(Spacer(1, 10))

        doc.build(story)
        pdf_bytes = buf.getvalue()
        logger.info(f"Cover letter PDF generated: {len(pdf_bytes):,} bytes")
        return pdf_bytes

    except ImportError:
        logger.warning("reportlab not installed — returning plain text bytes as fallback.")
        return cover_letter_text.encode("utf-8")
