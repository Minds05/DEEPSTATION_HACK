"""
Unit Tests — Phase 3: ATS Guard + Scorer
"""
import pytest
from app.browser.ats_guard import detect_ats, is_auto_apply_eligible, get_ats_label
from app.models.job import ATSType


# ── ATS detection tests ───────────────────────────────────────

class TestATSGuard:

    def test_lever_detection(self):
        assert detect_ats("https://jobs.lever.co/openai/abc123") == ATSType.LEVER

    def test_lever_short_domain(self):
        assert detect_ats("https://lever.co/company/role") == ATSType.LEVER

    def test_greenhouse_detection(self):
        assert detect_ats("https://boards.greenhouse.io/stripe/jobs/456") == ATSType.GREENHOUSE

    def test_greenhouse_short_domain(self):
        assert detect_ats("https://greenhouse.io/jobs/abc") == ATSType.GREENHOUSE

    def test_workday_detection(self):
        assert detect_ats("https://google.wd1.myworkdayjobs.com/en-US/careers") == ATSType.WORKDAY

    def test_workday_plain_domain(self):
        assert detect_ats("https://myworkdayjobs.com/company/job") == ATSType.WORKDAY

    def test_icims_is_other(self):
        assert detect_ats("https://careers.icims.com/jobs/1234") == ATSType.OTHER

    def test_smartrecruiters_is_other(self):
        assert detect_ats("https://jobs.smartrecruiters.com/company/role") == ATSType.OTHER

    def test_unknown_url_is_other(self):
        assert detect_ats("https://company.com/careers/role") == ATSType.OTHER

    def test_empty_url_is_other(self):
        assert detect_ats("") == ATSType.OTHER

    def test_none_safe(self):
        assert detect_ats(None) == ATSType.OTHER


# ── Auto-apply eligibility tests ──────────────────────────────

class TestAutoApplyEligibility:

    def test_lever_is_eligible(self):
        assert is_auto_apply_eligible(ATSType.LEVER) is True

    def test_greenhouse_is_eligible(self):
        assert is_auto_apply_eligible(ATSType.GREENHOUSE) is True

    def test_workday_not_eligible(self):
        assert is_auto_apply_eligible(ATSType.WORKDAY) is False

    def test_other_not_eligible(self):
        assert is_auto_apply_eligible(ATSType.OTHER) is False


# ── ATS label tests ───────────────────────────────────────────

class TestATSLabel:

    def test_lever_label(self):
        assert "Lever" in get_ats_label(ATSType.LEVER)
        assert "⚡" in get_ats_label(ATSType.LEVER)

    def test_workday_label(self):
        assert "Workday" in get_ats_label(ATSType.WORKDAY)
        assert "✍️" in get_ats_label(ATSType.WORKDAY)


# ── Scorer utility tests ──────────────────────────────────────

class TestScorerUtilities:

    def test_cosine_similarity_identical(self):
        from app.agents.scorer import _cosine_similarity
        vec = [1.0, 0.5, 0.25]
        assert abs(_cosine_similarity(vec, vec) - 1.0) < 1e-6

    def test_cosine_similarity_orthogonal(self):
        from app.agents.scorer import _cosine_similarity
        assert _cosine_similarity([1, 0], [0, 1]) == 0.0

    def test_cosine_similarity_zero_vector(self):
        from app.agents.scorer import _cosine_similarity
        assert _cosine_similarity([0, 0], [1, 2]) == 0.0

    def test_extract_json_block(self):
        from app.agents.scorer import _extract_json_block
        import json
        raw = '```json\n{"score": 87, "summary": "Good match."}\n```'
        data = json.loads(_extract_json_block(raw))
        assert data["score"] == 87

    def test_build_profile_text(self):
        from app.agents.scorer import _build_profile_text
        from app.models.resume import ResumeProfile
        profile = ResumeProfile(
            name="Alice", skills=["Python", "FastAPI"], seniority="Senior"
        )
        text = _build_profile_text(profile)
        assert "Python" in text
        assert "Senior" in text


# ── Query builder tests ───────────────────────────────────────

class TestJobHunterQueries:

    def test_query_contains_lever(self):
        from app.agents.job_hunter import build_search_queries
        from app.models.resume import ResumeProfile
        profile = ResumeProfile(name="X", skills=["Python"], seniority="Senior")
        queries = build_search_queries(profile, role="Backend Engineer", location="Bangalore")
        lever_queries = [q for q in queries if "lever" in q.lower()]
        assert len(lever_queries) >= 1

    def test_query_contains_greenhouse(self):
        from app.agents.job_hunter import build_search_queries
        from app.models.resume import ResumeProfile
        profile = ResumeProfile(name="X", skills=["Python"], seniority="Senior")
        queries = build_search_queries(profile, role="Backend Engineer")
        gh_queries = [q for q in queries if "greenhouse" in q.lower()]
        assert len(gh_queries) >= 1

    def test_infer_role_ml(self):
        from app.agents.job_hunter import _infer_role
        from app.models.resume import ResumeProfile
        profile = ResumeProfile(name="X", skills=["PyTorch", "LLM", "MLOps"], seniority="Senior")
        assert "AIML" in _infer_role(profile)

    def test_infer_role_devops(self):
        from app.agents.job_hunter import _infer_role
        from app.models.resume import ResumeProfile
        profile = ResumeProfile(name="X", skills=["Kubernetes", "Terraform", "GCP"], seniority="Mid")
        assert "DevOps" in _infer_role(profile)
