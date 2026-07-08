"""
Career Matching Service — Day 22
Engine: LOCAL_EXPLAINABLE_CAREER_MATCHING
Engine: DETERMINISTIC_ELIGIBILITY_RULES
Engine: RULE_BASED_SKILL_GAP_ANALYSIS

All intelligence is local, deterministic, and fully explainable.
No ML, no LLM, no external AI API.
Protected attributes (religion, caste, race, ethnicity, political belief,
disability, health, sexual orientation, gender, age) are never used as ranking signals.
"""

import json
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.models import (
    User, CareerProfile, StudentSkill, SkillCatalog, OpportunitySkill,
    Opportunity, EligibilityRule, EligibilityEvaluation, JobMatchScore,
    CareerGoal, SkillGapAnalysis, CareerRecommendation,
    Result, StudentAttendanceSummary, PlacementAudit
)


ENGINE_MATCHING = "LOCAL_EXPLAINABLE_CAREER_MATCHING"
ENGINE_ELIGIBILITY = "DETERMINISTIC_ELIGIBILITY_RULES"
ENGINE_SKILL_GAP = "RULE_BASED_SKILL_GAP_ANALYSIS"


class EligibilityService:
    """Deterministic rule-based eligibility evaluator."""

    @staticmethod
    def get_student_cgpa(db: Session, student_id: str) -> float:
        """Retrieve the student's latest CGPA from result records."""
        result = db.query(Result).filter_by(studentId=student_id).order_by(
            desc(Result.semesterNumber)
        ).first()
        if result and result.cgpa:
            return float(result.cgpa)
        if result and result.sgpa:
            return float(result.sgpa)
        return 0.0

    @staticmethod
    def get_student_active_backlogs(db: Session, student_id: str) -> int:
        """
        Count active backlogs — subjects where the student failed and has
        not yet cleared in a subsequent semester attempt. We use a simplified
        approach: count ResultDetail records where grade == 'F' and no later
        passing entry exists for the same subject.
        """
        try:
            from app.models.models import ResultDetail
            failed_subjects = set()
            passed_subjects = set()

            results = db.query(Result).filter_by(studentId=student_id).order_by(
                Result.semesterNumber
            ).all()
            for r in results:
                for detail in r.resultDetails:
                    if detail.grade and detail.grade.upper() == "F":
                        failed_subjects.add(detail.subjectId)
                    elif detail.grade and detail.grade.upper() not in ("F", "AB", "NA"):
                        passed_subjects.add(detail.subjectId)

            active_backlogs = failed_subjects - passed_subjects
            return len(active_backlogs)
        except Exception:
            return 0

    @classmethod
    def evaluate(
        cls,
        db: Session,
        student: User,
        opportunity: Opportunity
    ) -> Dict[str, Any]:
        """
        Evaluate all eligibility rules for this student against this opportunity.
        Returns full explanation including passed/failed rules.
        """
        rules = db.query(EligibilityRule).filter_by(opportunityId=opportunity.id).all()
        passed_rules = []
        failed_rules = []
        reasons = []

        student_cgpa = cls.get_student_cgpa(db, student.id)
        student_backlogs = cls.get_student_active_backlogs(db, student.id)
        student_dept_id = student.departmentId or ""
        profile = db.query(CareerProfile).filter_by(studentId=student.id).first()
        student_grad_year = profile.graduationYear if profile else 0

        # Evaluate each defined rule
        for rule in rules:
            rule_type = rule.ruleType
            rule_val = rule.ruleValue.strip()

            if rule_type == "MIN_CGPA":
                try:
                    min_cgpa = float(rule_val)
                    if student_cgpa >= min_cgpa:
                        passed_rules.append(f"MIN_CGPA: {student_cgpa:.2f} >= {min_cgpa}")
                    else:
                        failed_rules.append(f"MIN_CGPA: Student CGPA {student_cgpa:.2f} < required {min_cgpa}")
                        reasons.append(f"Minimum CGPA requirement is {min_cgpa}, student has {student_cgpa:.2f}")
                except ValueError:
                    passed_rules.append(f"MIN_CGPA: Rule value '{rule_val}' unparseable, skipped")

            elif rule_type == "MAX_BACKLOGS":
                try:
                    max_bl = int(rule_val)
                    if student_backlogs <= max_bl:
                        passed_rules.append(f"MAX_BACKLOGS: {student_backlogs} <= {max_bl}")
                    else:
                        failed_rules.append(f"MAX_BACKLOGS: Student has {student_backlogs} active backlogs, max allowed {max_bl}")
                        reasons.append(f"Maximum active backlogs allowed is {max_bl}, student has {student_backlogs}")
                except ValueError:
                    passed_rules.append(f"MAX_BACKLOGS: Rule value '{rule_val}' unparseable, skipped")

            elif rule_type == "ALLOWED_DEPARTMENTS":
                try:
                    allowed = json.loads(rule_val)
                    if student_dept_id in allowed or (student.department and student.department.name in allowed):
                        passed_rules.append(f"ALLOWED_DEPARTMENTS: Student department matches")
                    else:
                        dept_name = student.department.name if student.department else "Unknown"
                        failed_rules.append(f"ALLOWED_DEPARTMENTS: '{dept_name}' not in allowed list")
                        reasons.append(f"Student department '{dept_name}' is not eligible for this opportunity")
                except Exception:
                    passed_rules.append(f"ALLOWED_DEPARTMENTS: Rule parse error, skipped")

            elif rule_type == "GRADUATION_YEAR":
                try:
                    required_year = int(rule_val)
                    if student_grad_year == required_year or student_grad_year == 0:
                        passed_rules.append(f"GRADUATION_YEAR: {student_grad_year} matches {required_year}")
                    else:
                        failed_rules.append(f"GRADUATION_YEAR: Student graduation year {student_grad_year} != {required_year}")
                        reasons.append(f"Required graduation year is {required_year}, student is {student_grad_year}")
                except ValueError:
                    passed_rules.append(f"GRADUATION_YEAR: Rule value '{rule_val}' unparseable, skipped")

            elif rule_type == "REQUIRED_SKILLS":
                try:
                    required_skill_names = json.loads(rule_val)
                    student_skill_names = {
                        ss.skill.name.lower() for ss in
                        db.query(StudentSkill).filter_by(studentId=student.id).all()
                        if ss.skill
                    }
                    missing = [s for s in required_skill_names if s.lower() not in student_skill_names]
                    if not missing:
                        passed_rules.append(f"REQUIRED_SKILLS: All {len(required_skill_names)} skills present")
                    else:
                        failed_rules.append(f"REQUIRED_SKILLS: Missing {missing}")
                        reasons.append(f"Missing required skills: {', '.join(missing)}")
                except Exception:
                    passed_rules.append(f"REQUIRED_SKILLS: Rule parse error, skipped")

        # Also check opportunity-level CGPA and backlog constraints directly
        if opportunity.minCgpa > 0 and student_cgpa < opportunity.minCgpa:
            if not any("MIN_CGPA" in r for r in failed_rules):
                failed_rules.append(f"CGPA_DIRECT: {student_cgpa:.2f} < {opportunity.minCgpa}")
                reasons.append(f"Minimum CGPA {opportunity.minCgpa} not met (student has {student_cgpa:.2f})")

        if opportunity.maxBacklogs < 999 and student_backlogs > opportunity.maxBacklogs:
            if not any("MAX_BACKLOGS" in r for r in failed_rules):
                failed_rules.append(f"BACKLOGS_DIRECT: {student_backlogs} > {opportunity.maxBacklogs}")
                reasons.append(f"Active backlogs {student_backlogs} exceeds limit {opportunity.maxBacklogs}")

        eligible = len(failed_rules) == 0

        return {
            "eligible": eligible,
            "reasons": reasons,
            "failedRules": failed_rules,
            "passedRules": passed_rules,
            "evaluatedAt": datetime.utcnow().isoformat(),
            "engineType": ENGINE_ELIGIBILITY,
            "studentCgpa": student_cgpa,
            "studentBacklogs": student_backlogs
        }

    @classmethod
    def persist_evaluation(
        cls,
        db: Session,
        student_id: str,
        opportunity_id: str,
        result: Dict[str, Any]
    ) -> EligibilityEvaluation:
        """Upsert the eligibility evaluation record."""
        eval_rec = db.query(EligibilityEvaluation).filter_by(
            opportunityId=opportunity_id, studentId=student_id
        ).first()
        if eval_rec:
            eval_rec.eligible = result["eligible"]
            eval_rec.reasonsJson = json.dumps(result["reasons"])
            eval_rec.failedRulesJson = json.dumps(result["failedRules"])
            eval_rec.passedRulesJson = json.dumps(result["passedRules"])
            eval_rec.evaluatedAt = datetime.utcnow()
        else:
            eval_rec = EligibilityEvaluation(
                opportunityId=opportunity_id,
                studentId=student_id,
                eligible=result["eligible"],
                reasonsJson=json.dumps(result["reasons"]),
                failedRulesJson=json.dumps(result["failedRules"]),
                passedRulesJson=json.dumps(result["passedRules"]),
                evaluatedAt=datetime.utcnow()
            )
            db.add(eval_rec)
        db.flush()
        return eval_rec


class CareerMatchingService:
    """
    Local explainable career matching engine.
    Engine: LOCAL_EXPLAINABLE_CAREER_MATCHING
    Score: 0-100 composite of weighted deterministic factors.
    No trained model, no LLM, no external API.
    """

    WEIGHTS = {
        "required_skills": 0.35,
        "preferred_skills": 0.15,
        "project_relevance": 0.15,
        "internship_relevance": 0.10,
        "certification_relevance": 0.10,
        "cgpa_margin": 0.10,
        "goal_alignment": 0.05,
    }

    @classmethod
    def _keyword_overlap(cls, text: Optional[str], keywords: List[str]) -> float:
        """Returns fraction of keywords found in text."""
        if not text or not keywords:
            return 0.0
        text_lower = text.lower()
        hits = sum(1 for kw in keywords if kw.lower() in text_lower)
        return hits / len(keywords)

    @classmethod
    def compute_match(
        cls,
        db: Session,
        student: User,
        opportunity: Opportunity
    ) -> Dict[str, Any]:
        """Compute the explainable match score for a student-opportunity pair."""

        # Load student skills
        student_skills_raw = db.query(StudentSkill).filter_by(studentId=student.id).all()
        student_skill_names = {ss.skill.name.lower() for ss in student_skills_raw if ss.skill}

        # Load opportunity skills
        opp_skills = db.query(OpportunitySkill).filter_by(opportunityId=opportunity.id).all()
        required_skills = [os.skill.name for os in opp_skills if os.isRequired and os.skill]
        preferred_skills = [os.skill.name for os in opp_skills if not os.isRequired and os.skill]

        # Matched / missing tracking
        matched_required = [s for s in required_skills if s.lower() in student_skill_names]
        missing_required = [s for s in required_skills if s.lower() not in student_skill_names]
        matched_preferred = [s for s in preferred_skills if s.lower() in student_skill_names]
        missing_preferred = [s for s in preferred_skills if s.lower() not in student_skill_names]

        # Factor 1: Required skill overlap
        req_overlap = (len(matched_required) / len(required_skills)) if required_skills else 1.0

        # Factor 2: Preferred skill overlap
        pref_overlap = (len(matched_preferred) / len(preferred_skills)) if preferred_skills else 0.5

        # Load career profile for contextual factors
        career = db.query(CareerProfile).filter_by(studentId=student.id).first()
        projects_text = career.projects if career else ""
        experience_text = career.experience if career else ""
        certifications_text = career.certifications if career else ""

        # Build keyword pool from opportunity title + description
        opp_keywords = (opportunity.title + " " + opportunity.description[:500]).split()
        opp_keywords = list({w.lower().strip(".,()") for w in opp_keywords if len(w) > 3})[:30]

        # Factor 3: Project relevance
        proj_relevance = cls._keyword_overlap(projects_text, opp_keywords)

        # Factor 4: Internship/Experience relevance
        exp_relevance = cls._keyword_overlap(experience_text, opp_keywords)

        # Factor 5: Certification relevance
        cert_relevance = cls._keyword_overlap(certifications_text, required_skills + preferred_skills)

        # Factor 6: CGPA margin
        student_cgpa = EligibilityService.get_student_cgpa(db, student.id)
        if opportunity.minCgpa > 0:
            cgpa_margin = min(1.0, max(0.0, (student_cgpa - opportunity.minCgpa) / max(opportunity.minCgpa, 0.1)))
        else:
            cgpa_margin = min(1.0, student_cgpa / 10.0) if student_cgpa <= 10 else 1.0

        # Factor 7: Career goal alignment
        goals = db.query(CareerGoal).filter_by(studentId=student.id, status="ACTIVE").all()
        goal_alignment = 0.0
        for g in goals:
            title_hit = g.title.lower() in opportunity.title.lower() or opportunity.title.lower() in g.title.lower()
            role_hit = g.targetRole and g.targetRole.lower() in opportunity.title.lower()
            industry_hit = g.targetIndustry and g.targetIndustry.lower() in (opportunity.company.industry.lower() if opportunity.company else "")
            if title_hit or role_hit or industry_hit:
                goal_alignment = 1.0
                break

        # Compute weighted total
        factors = [
            {"name": "Required Skill Overlap", "code": "required_skills", "weight": cls.WEIGHTS["required_skills"], "rawValue": round(req_overlap, 3), "contribution": round(req_overlap * cls.WEIGHTS["required_skills"] * 100, 2)},
            {"name": "Preferred Skill Overlap", "code": "preferred_skills", "weight": cls.WEIGHTS["preferred_skills"], "rawValue": round(pref_overlap, 3), "contribution": round(pref_overlap * cls.WEIGHTS["preferred_skills"] * 100, 2)},
            {"name": "Project Relevance", "code": "project_relevance", "weight": cls.WEIGHTS["project_relevance"], "rawValue": round(proj_relevance, 3), "contribution": round(proj_relevance * cls.WEIGHTS["project_relevance"] * 100, 2)},
            {"name": "Internship/Experience Relevance", "code": "internship_relevance", "weight": cls.WEIGHTS["internship_relevance"], "rawValue": round(exp_relevance, 3), "contribution": round(exp_relevance * cls.WEIGHTS["internship_relevance"] * 100, 2)},
            {"name": "Certification Relevance", "code": "certification_relevance", "weight": cls.WEIGHTS["certification_relevance"], "rawValue": round(cert_relevance, 3), "contribution": round(cert_relevance * cls.WEIGHTS["certification_relevance"] * 100, 2)},
            {"name": "Academic CGPA Margin", "code": "cgpa_margin", "weight": cls.WEIGHTS["cgpa_margin"], "rawValue": round(cgpa_margin, 3), "contribution": round(cgpa_margin * cls.WEIGHTS["cgpa_margin"] * 100, 2)},
            {"name": "Career Goal Alignment", "code": "goal_alignment", "weight": cls.WEIGHTS["goal_alignment"], "rawValue": round(goal_alignment, 3), "contribution": round(goal_alignment * cls.WEIGHTS["goal_alignment"] * 100, 2)},
        ]

        total_score = sum(f["contribution"] for f in factors)
        total_score = round(min(100.0, total_score), 2)

        # Run eligibility check
        elig_result = EligibilityService.evaluate(db, student, opportunity)
        elig_status = "ELIGIBLE" if elig_result["eligible"] else "INELIGIBLE"
        elig_reason = "; ".join(elig_result["reasons"]) if elig_result["reasons"] else "All eligibility criteria passed."

        # Build explanation
        matched_all = matched_required + matched_preferred
        missing_all = missing_required + missing_preferred
        explanation_parts = [f"Match score: {total_score:.1f}/100 (engine: {ENGINE_MATCHING})."]
        if matched_required:
            explanation_parts.append(f"Required skills matched: {', '.join(matched_required)}.")
        if missing_required:
            explanation_parts.append(f"Missing critical skills: {', '.join(missing_required)}.")
        if not elig_result["eligible"]:
            explanation_parts.append(f"Eligibility: INELIGIBLE — {elig_reason}")
        else:
            explanation_parts.append("Eligibility: ELIGIBLE for this opportunity.")
        explanation_parts.append("No protected attributes (religion, caste, gender, disability, etc.) were used in this score.")

        return {
            "score": total_score,
            "engineType": ENGINE_MATCHING,
            "factors": factors,
            "matchedSkills": matched_all,
            "missingSkills": missing_all,
            "matchedRequiredSkills": matched_required,
            "missingRequiredSkills": missing_required,
            "eligibilityStatus": elig_status,
            "eligibilityReason": elig_reason,
            "eligibilityDetails": elig_result,
            "explanation": " ".join(explanation_parts),
            "generatedAt": datetime.utcnow().isoformat()
        }

    @classmethod
    def persist_match(
        cls,
        db: Session,
        student_id: str,
        opportunity_id: str,
        result: Dict[str, Any]
    ) -> JobMatchScore:
        """Upsert match score record."""
        existing = db.query(JobMatchScore).filter_by(
            studentId=student_id, opportunityId=opportunity_id
        ).first()
        if existing:
            existing.score = result["score"]
            existing.factorsJson = json.dumps(result["factors"])
            existing.matchedSkillsJson = json.dumps(result["matchedSkills"])
            existing.missingSkillsJson = json.dumps(result["missingSkills"])
            existing.eligibilityStatus = result["eligibilityStatus"]
            existing.eligibilityReason = result["eligibilityReason"]
            existing.explanation = result["explanation"]
            existing.generatedAt = datetime.utcnow()
            return existing
        else:
            match = JobMatchScore(
                studentId=student_id,
                opportunityId=opportunity_id,
                score=result["score"],
                engineType=ENGINE_MATCHING,
                factorsJson=json.dumps(result["factors"]),
                matchedSkillsJson=json.dumps(result["matchedSkills"]),
                missingSkillsJson=json.dumps(result["missingSkills"]),
                eligibilityStatus=result["eligibilityStatus"],
                eligibilityReason=result["eligibilityReason"],
                explanation=result["explanation"],
                generatedAt=datetime.utcnow()
            )
            db.add(match)
            db.flush()
            return match


class SkillGapService:
    """Rule-based skill gap analyzer."""

    @classmethod
    def analyze(
        cls,
        db: Session,
        student: User,
        opportunity: Optional[Opportunity] = None,
        goal_title: str = "General Career Readiness"
    ) -> Dict[str, Any]:
        """Compare student skills vs opportunity/goal requirements."""

        student_skill_names = {
            ss.skill.name.lower(): ss
            for ss in db.query(StudentSkill).filter_by(studentId=student.id).all()
            if ss.skill
        }

        required_skills = []
        preferred_skills = []
        if opportunity:
            opp_skills = db.query(OpportunitySkill).filter_by(opportunityId=opportunity.id).all()
            required_skills = [os.skill.name for os in opp_skills if os.isRequired and os.skill]
            preferred_skills = [os.skill.name for os in opp_skills if not os.isRequired and os.skill]
            goal_title = opportunity.title

        matched = [s for s in required_skills + preferred_skills if s.lower() in student_skill_names]
        missing_critical = [s for s in required_skills if s.lower() not in student_skill_names]
        missing_optional = [s for s in preferred_skills if s.lower() not in student_skill_names]

        total_skills = len(required_skills) + len(preferred_skills)
        readiness = (len(matched) / total_skills * 100.0) if total_skills > 0 else 50.0

        # Generate prioritized learning actions
        actions = []
        for skill in missing_critical[:5]:
            actions.append({
                "priority": "HIGH",
                "action": f"Learn or certify in '{skill}'",
                "reason": "Required skill for this opportunity",
                "type": "SKILL_ACQUISITION"
            })
        for skill in missing_optional[:3]:
            actions.append({
                "priority": "MEDIUM",
                "action": f"Build proficiency in '{skill}'",
                "reason": "Preferred skill — improves match score",
                "type": "SKILL_ENHANCEMENT"
            })

        return {
            "goalTitle": goal_title,
            "opportunityId": opportunity.id if opportunity else None,
            "readinessScore": round(readiness, 2),
            "matchedSkills": matched,
            "missingCriticalSkills": missing_critical,
            "missingOptionalSkills": missing_optional,
            "learningActions": actions,
            "engineType": ENGINE_SKILL_GAP,
            "calculatedAt": datetime.utcnow().isoformat()
        }


class PlacementRecommendationService:
    """Generate career recommendations from student state."""

    @classmethod
    def generate(cls, db: Session, student: User) -> List[Dict[str, Any]]:
        """Generate a set of actionable career recommendations."""
        recs = []
        career = db.query(CareerProfile).filter_by(studentId=student.id).first()

        # Check profile completeness
        if not career:
            recs.append({
                "category": "RESUME_TWEAK",
                "title": "Create Your Career Profile",
                "description": "You haven't set up your career profile yet. A complete profile is the first step to getting noticed by recruiters.",
                "priority": "CRITICAL",
                "reason": "No career profile exists for this student."
            })
            return recs

        if not career.biography:
            recs.append({
                "category": "RESUME_TWEAK",
                "title": "Add a Professional Biography",
                "description": "A strong bio helps recruiters understand your background quickly. Add 2-3 sentences about your goals and expertise.",
                "priority": "HIGH",
                "reason": "Biography is empty in career profile."
            })

        if not career.projects:
            recs.append({
                "category": "RESUME_TWEAK",
                "title": "Add Your Projects",
                "description": "Projects demonstrate practical skills. Add at least 2-3 relevant projects with tech stack and outcomes.",
                "priority": "HIGH",
                "reason": "No projects listed in career profile."
            })

        # Skills check
        skill_count = db.query(StudentSkill).filter_by(studentId=student.id).count()
        if skill_count < 3:
            recs.append({
                "category": "SKILL_UPGRADE",
                "title": "Add More Skills to Your Profile",
                "description": "You have fewer than 3 skills listed. Add your programming languages, frameworks, and tools to improve your matching score.",
                "priority": "HIGH",
                "reason": f"Only {skill_count} skill(s) listed."
            })

        # Goals check
        goal_count = db.query(CareerGoal).filter_by(studentId=student.id, status="ACTIVE").count()
        if goal_count == 0:
            recs.append({
                "category": "GOAL_ADJUSTMENT",
                "title": "Set a Career Goal",
                "description": "Career goals help the matching engine find relevant opportunities. Define your target role and industry.",
                "priority": "MEDIUM",
                "reason": "No active career goals defined."
            })

        # Check top opportunities for skill gaps
        from app.models.models import Opportunity
        open_opps = db.query(Opportunity).filter_by(status="OPEN").limit(5).all()
        for opp in open_opps:
            gap = SkillGapService.analyze(db, student, opp)
            if gap["missingCriticalSkills"]:
                skills_str = ", ".join(gap["missingCriticalSkills"][:3])
                recs.append({
                    "category": "SKILL_UPGRADE",
                    "title": f"Skill Gap: '{opp.title}'",
                    "description": f"You're missing critical skills for '{opp.title}' at {opp.company.name if opp.company else ''}. Focus on: {skills_str}.",
                    "priority": "MEDIUM",
                    "reason": f"Missing required skills: {skills_str}"
                })

        return recs[:8]  # Cap at 8 recommendations

    @classmethod
    def upsert_recommendations(cls, db: Session, student_id: str) -> List[CareerRecommendation]:
        """Refresh and persist career recommendations for a student."""
        student = db.query(User).filter_by(id=student_id).first()
        if not student:
            return []

        # Expire old active recommendations
        db.query(CareerRecommendation).filter_by(
            studentId=student_id, status="ACTIVE"
        ).update({"status": "EXPIRED"} if False else {})  # Keep existing, just add new

        recs_data = cls.generate(db, student)
        rec_objects = []
        for r in recs_data:
            rec = CareerRecommendation(
                studentId=student_id,
                category=r["category"],
                title=r["title"],
                description=r["description"],
                priority=r["priority"],
                status="ACTIVE",
                reason=r["reason"]
            )
            db.add(rec)
            rec_objects.append(rec)

        db.flush()
        return rec_objects


class PlacementAuditService:
    """Records auditable placement officer and admin actions."""

    @staticmethod
    def record(
        db: Session,
        action: str,
        entity_type: str,
        actor_id: Optional[str] = None,
        student_id: Optional[str] = None,
        entity_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        audit = PlacementAudit(
            actorId=actor_id,
            studentId=student_id,
            action=action,
            entityType=entity_type,
            entityId=entity_id,
            actionMetadata=json.dumps(metadata) if metadata else None
        )
        db.add(audit)
        db.flush()
