"""
Day 22 pytest suite — Enterprise Placement & Career Intelligence System
Tests: model imports, service logic, API endpoint schemas
"""
import pytest
import json
from unittest.mock import MagicMock, patch
from datetime import datetime

# ──────────────────────────────────────────────
# 1. Model import tests
# ──────────────────────────────────────────────

def test_career_profile_model_import():
    from app.models.models import CareerProfile
    assert CareerProfile.__tablename__ == "CareerProfile"

def test_skill_catalog_model_import():
    from app.models.models import SkillCatalog
    assert SkillCatalog.__tablename__ == "SkillCatalog"

def test_student_skill_model_import():
    from app.models.models import StudentSkill
    assert StudentSkill.__tablename__ == "StudentSkill"

def test_resume_profile_model_import():
    from app.models.models import ResumeProfile
    assert ResumeProfile.__tablename__ == "ResumeProfile"

def test_resume_version_model_import():
    from app.models.models import ResumeVersion
    assert ResumeVersion.__tablename__ == "ResumeVersion"

def test_company_model_import():
    from app.models.models import Company
    assert Company.__tablename__ == "Company"

def test_recruiter_model_import():
    from app.models.models import RecruiterContact
    assert RecruiterContact.__tablename__ == "RecruiterContact"

def test_opportunity_model_import():
    from app.models.models import Opportunity
    assert Opportunity.__tablename__ == "Opportunity"

def test_opportunity_skill_model_import():
    from app.models.models import OpportunitySkill
    assert OpportunitySkill.__tablename__ == "OpportunitySkill"

def test_eligibility_rule_model_import():
    from app.models.models import EligibilityRule
    assert EligibilityRule.__tablename__ == "EligibilityRule"

def test_eligibility_evaluation_model_import():
    from app.models.models import EligibilityEvaluation
    assert EligibilityEvaluation.__tablename__ == "EligibilityEvaluation"

def test_placement_drive_model_import():
    from app.models.models import PlacementDrive
    assert PlacementDrive.__tablename__ == "PlacementDrive"

def test_drive_registration_model_import():
    from app.models.models import DriveRegistration
    assert DriveRegistration.__tablename__ == "DriveRegistration"

def test_job_application_model_import():
    from app.models.models import JobApplication
    assert JobApplication.__tablename__ == "JobApplication"

def test_application_status_history_model_import():
    from app.models.models import ApplicationStatusHistory
    assert ApplicationStatusHistory.__tablename__ == "ApplicationStatusHistory"

def test_interview_round_model_import():
    from app.models.models import InterviewRound
    assert InterviewRound.__tablename__ == "InterviewRound"

def test_interview_feedback_model_import():
    from app.models.models import InterviewFeedback
    assert InterviewFeedback.__tablename__ == "InterviewFeedback"

def test_offer_model_import():
    from app.models.models import Offer
    assert Offer.__tablename__ == "Offer"

def test_placement_outcome_model_import():
    from app.models.models import PlacementOutcome
    assert PlacementOutcome.__tablename__ == "PlacementOutcome"

def test_career_goal_model_import():
    from app.models.models import CareerGoal
    assert CareerGoal.__tablename__ == "CareerGoal"

def test_skill_gap_analysis_model_import():
    from app.models.models import SkillGapAnalysis
    assert SkillGapAnalysis.__tablename__ == "SkillGapAnalysis"

def test_career_recommendation_model_import():
    from app.models.models import CareerRecommendation
    assert CareerRecommendation.__tablename__ == "CareerRecommendation"

def test_job_match_score_model_import():
    from app.models.models import JobMatchScore
    assert JobMatchScore.__tablename__ == "JobMatchScore"

def test_placement_audit_model_import():
    from app.models.models import PlacementAudit
    assert PlacementAudit.__tablename__ == "PlacementAudit"


# ──────────────────────────────────────────────
# 2. Service import tests
# ──────────────────────────────────────────────

def test_career_matching_service_import():
    from app.services.career_matching_service import CareerMatchingService
    assert hasattr(CareerMatchingService, "compute_match")

def test_eligibility_service_import():
    from app.services.career_matching_service import EligibilityService
    assert hasattr(EligibilityService, "evaluate")

def test_skill_gap_service_import():
    from app.services.career_matching_service import SkillGapService
    assert hasattr(SkillGapService, "analyze")

def test_placement_recommendation_service_import():
    from app.services.career_matching_service import PlacementRecommendationService
    assert hasattr(PlacementRecommendationService, "generate")

def test_placement_audit_service_import():
    from app.services.career_matching_service import PlacementAuditService
    assert hasattr(PlacementAuditService, "record")


# ──────────────────────────────────────────────
# 3. Engine constant tests
# ──────────────────────────────────────────────

def test_engine_label_matching():
    from app.services.career_matching_service import ENGINE_MATCHING
    assert ENGINE_MATCHING == "LOCAL_EXPLAINABLE_CAREER_MATCHING"

def test_engine_label_eligibility():
    from app.services.career_matching_service import ENGINE_ELIGIBILITY
    assert ENGINE_ELIGIBILITY == "DETERMINISTIC_ELIGIBILITY_RULES"

def test_engine_label_skill_gap():
    from app.services.career_matching_service import ENGINE_SKILL_GAP
    assert ENGINE_SKILL_GAP == "RULE_BASED_SKILL_GAP_ANALYSIS"


# ──────────────────────────────────────────────
# 4. Matching weight tests (weights sum to 1.0)
# ──────────────────────────────────────────────

def test_matching_weights_sum_to_one():
    from app.services.career_matching_service import CareerMatchingService
    total = sum(CareerMatchingService.WEIGHTS.values())
    assert abs(total - 1.0) < 0.001, f"Weights sum to {total}, expected 1.0"

def test_matching_weights_keys():
    from app.services.career_matching_service import CareerMatchingService
    expected_keys = {"required_skills", "preferred_skills", "project_relevance",
                     "internship_relevance", "certification_relevance", "cgpa_margin", "goal_alignment"}
    assert set(CareerMatchingService.WEIGHTS.keys()) == expected_keys

def test_no_protected_attributes_in_weights():
    from app.services.career_matching_service import CareerMatchingService
    protected = {"gender", "religion", "caste", "race", "ethnicity", "disability",
                 "health", "sexual_orientation", "political"}
    for key in CareerMatchingService.WEIGHTS:
        for attr in protected:
            assert attr not in key.lower(), f"Protected attribute '{attr}' found in weight key '{key}'"


# ──────────────────────────────────────────────
# 5. Keyword overlap utility tests
# ──────────────────────────────────────────────

def test_keyword_overlap_full_match():
    from app.services.career_matching_service import CareerMatchingService
    result = CareerMatchingService._keyword_overlap("python django sql", ["python", "sql"])
    assert result == 1.0

def test_keyword_overlap_partial():
    from app.services.career_matching_service import CareerMatchingService
    result = CareerMatchingService._keyword_overlap("python only", ["python", "sql"])
    assert result == 0.5

def test_keyword_overlap_none():
    from app.services.career_matching_service import CareerMatchingService
    result = CareerMatchingService._keyword_overlap("java spring", ["python", "sql"])
    assert result == 0.0

def test_keyword_overlap_empty_text():
    from app.services.career_matching_service import CareerMatchingService
    result = CareerMatchingService._keyword_overlap("", ["python"])
    assert result == 0.0

def test_keyword_overlap_empty_keywords():
    from app.services.career_matching_service import CareerMatchingService
    result = CareerMatchingService._keyword_overlap("python django", [])
    assert result == 0.0


# ──────────────────────────────────────────────
# 6. Router import tests
# ──────────────────────────────────────────────

def test_placement_router_import():
    from app.api.v1.endpoints.placements import router
    assert router is not None

def test_placement_router_routes_exist():
    from app.api.v1.endpoints.placements import router
    paths = [route.path for route in router.routes]
    assert "/career-profile/me" in paths
    assert "/opportunities" in paths
    assert "/applications" in paths

def test_placement_router_registered_in_main_router():
    from app.api.v1.router import api_router
    tags = [tag for route in api_router.routes for tag in (route.tags if hasattr(route, "tags") else [])]
    assert "Enterprise Placement & Career Intelligence" in tags


# ──────────────────────────────────────────────
# 7. Pydantic schema tests
# ──────────────────────────────────────────────

def test_career_profile_create_schema():
    from app.api.v1.endpoints.placements import CareerProfileCreate
    payload = CareerProfileCreate(graduationYear=2025)
    assert payload.graduationYear == 2025
    assert payload.biography is None

def test_opportunity_create_schema():
    from app.api.v1.endpoints.placements import OpportunityCreate
    payload = OpportunityCreate(
        companyId="c1",
        title="SWE",
        description="Software Engineer",
        type="JOB",
        location="Bangalore",
        compensation="18 LPA"
    )
    assert payload.type == "JOB"
    assert payload.minCgpa == 0.0
    assert payload.maxBacklogs == 999

def test_application_status_update_schema():
    from app.api.v1.endpoints.placements import ApplicationStatusUpdate
    p = ApplicationStatusUpdate(status="SHORTLISTED", notes="Impressive profile")
    assert p.status == "SHORTLISTED"

def test_offer_create_schema():
    from app.api.v1.endpoints.placements import OfferCreate
    from datetime import datetime
    p = OfferCreate(
        applicationId="app1",
        packageAmount=18.0,
        deadline=datetime(2025, 12, 31)
    )
    assert p.packageAmount == 18.0

def test_recommendation_status_patch():
    from app.api.v1.endpoints.placements import RecommendationStatusPatch
    p = RecommendationStatusPatch(status="ACCEPTED")
    assert p.status == "ACCEPTED"


# ──────────────────────────────────────────────
# 8. Eligibility evaluate logic unit tests (mock DB)
# ──────────────────────────────────────────────

def make_mock_student(cgpa=7.5, dept_id="dept1", dept_name="CSE"):
    student = MagicMock()
    student.id = "stu1"
    student.departmentId = dept_id
    dept = MagicMock()
    dept.name = dept_name
    student.department = dept
    return student

def make_mock_opportunity(min_cgpa=6.0, max_backlogs=999):
    opp = MagicMock()
    opp.id = "opp1"
    opp.minCgpa = min_cgpa
    opp.maxBacklogs = max_backlogs
    return opp

def test_eligibility_cgpa_pass():
    from app.services.career_matching_service import EligibilityService
    db = MagicMock()
    db.query.return_value.filter_by.return_value.order_by.return_value.first.return_value = None
    db.query.return_value.filter_by.return_value.all.return_value = []
    student = make_mock_student(cgpa=7.5)
    opp = make_mock_opportunity(min_cgpa=6.0)
    db.query.return_value.filter_by.return_value.all.return_value = []  # no rules
    # Patch the CGPA getter
    with patch.object(EligibilityService, "get_student_cgpa", return_value=7.5):
        with patch.object(EligibilityService, "get_student_active_backlogs", return_value=0):
            result = EligibilityService.evaluate(db, student, opp)
    assert result["eligible"] is True

def test_eligibility_cgpa_fail():
    from app.services.career_matching_service import EligibilityService
    db = MagicMock()
    db.query.return_value.filter_by.return_value.order_by.return_value.first.return_value = None
    db.query.return_value.filter_by.return_value.all.return_value = []
    student = make_mock_student()
    opp = make_mock_opportunity(min_cgpa=8.0)
    with patch.object(EligibilityService, "get_student_cgpa", return_value=7.0):
        with patch.object(EligibilityService, "get_student_active_backlogs", return_value=0):
            result = EligibilityService.evaluate(db, student, opp)
    assert result["eligible"] is False
    assert any("CGPA" in r for r in result["reasons"])

def test_eligibility_backlog_fail():
    from app.services.career_matching_service import EligibilityService
    db = MagicMock()
    db.query.return_value.filter_by.return_value.all.return_value = []
    student = make_mock_student()
    opp = make_mock_opportunity(min_cgpa=0, max_backlogs=2)
    with patch.object(EligibilityService, "get_student_cgpa", return_value=8.0):
        with patch.object(EligibilityService, "get_student_active_backlogs", return_value=3):
            result = EligibilityService.evaluate(db, student, opp)
    assert result["eligible"] is False

def test_eligibility_engine_type_label():
    from app.services.career_matching_service import EligibilityService
    db = MagicMock()
    db.query.return_value.filter_by.return_value.all.return_value = []
    student = make_mock_student()
    opp = make_mock_opportunity()
    with patch.object(EligibilityService, "get_student_cgpa", return_value=8.0):
        with patch.object(EligibilityService, "get_student_active_backlogs", return_value=0):
            result = EligibilityService.evaluate(db, student, opp)
    assert result["engineType"] == "DETERMINISTIC_ELIGIBILITY_RULES"
