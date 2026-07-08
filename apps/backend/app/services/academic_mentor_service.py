import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text, desc

from app.models.models import (
    User, Subject, StudentAttendanceSummary, StudentResult, StudentAssignment, Result,
    AcademicMentorProfile, AcademicInsight, AcademicRiskAssessment, AcademicRiskFactor,
    StudyRecommendation, StudyPlan, StudyPlanItem, MentorIntervention, AcademicMentorAudit
)
from app.services.notification_service import NotificationService

class AcademicMentorService:
    @staticmethod
    def record_mentor_audit(
        db: Session,
        action: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        actor_id: Optional[str] = None,
        student_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> AcademicMentorAudit:
        """Helper to create audit log records for academic mentor actions."""
        audit = AcademicMentorAudit(
            actorId=actor_id,
            studentId=student_id,
            action=action,
            entityType=entity_type,
            entityId=entity_id,
            actionMetadata=json.dumps(metadata) if metadata else None,
            ipAddress=ip_address,
            createdAt=datetime.utcnow()
        )
        db.add(audit)
        db.commit()
        db.refresh(audit)
        return audit

    @staticmethod
    def collect_student_academic_data(db: Session, student_id: str) -> Optional[Dict[str, Any]]:
        """Collects all available academic records for a student."""
        student = db.query(User).filter(User.id == student_id).first()
        if not student:
            return None

        attendance = db.query(StudentAttendanceSummary).filter(StudentAttendanceSummary.userId == student_id).all()
        student_results = db.query(StudentResult).filter(StudentResult.userId == student_id).all()
        results = db.query(Result).filter(Result.studentId == student_id).order_by(Result.semesterNumber.asc()).all()
        assignments = db.query(StudentAssignment).filter(StudentAssignment.userId == student_id).all()

        return {
            "student": student,
            "attendance": attendance,
            "student_results": student_results,
            "results": results,
            "assignments": assignments
        }

    @staticmethod
    def calculate_data_completeness(data: Dict[str, Any]) -> float:
        """Calculates percentage of academic records populated for the student."""
        completeness = 0.0
        # If student exists, check categories
        if len(data.get("attendance", [])) > 0:
            completeness += 34.0
        if len(data.get("student_results", [])) > 0 or len(data.get("results", [])) > 0:
            completeness += 33.0
        if len(data.get("assignments", [])) > 0:
            completeness += 33.0
        return completeness

    @staticmethod
    def calculate_attendance_metrics(data: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregates attendance metrics across subjects."""
        attendance = data.get("attendance", [])
        if not attendance:
            return {"overall_rate": 100.0, "concern_subjects": []}

        total_pct = 0.0
        concern_subjects = []
        for summary in attendance:
            total_pct += summary.percentage
            if summary.percentage < 75.0:
                concern_subjects.append({
                    "subjectId": summary.subjectId,
                    "percentage": summary.percentage
                })

        overall = total_pct / len(attendance)
        return {
            "overall_rate": round(overall, 2),
            "concern_subjects": concern_subjects
        }

    @staticmethod
    def calculate_subject_performance(data: Dict[str, Any]) -> Dict[str, Any]:
        """Extracts failed subjects and overall grade performance."""
        results = data.get("student_results", [])
        fail_subjects = []
        failed_count = 0
        total_score = 0.0
        count = 0

        # Grade to point mappings for local analytics calculation
        grade_points = {"O": 10, "A+": 9, "A": 8, "B+": 7, "B": 6, "C": 5, "P": 4, "F": 0}

        for res in results:
            # Internal & External marks out of 100
            total_marks = res.internalMarks + res.externalMarks
            total_score += total_marks
            count += 1

            is_fail = (res.grade == "F") or (total_marks < 40)
            if is_fail:
                failed_count += 1
                fail_subjects.append({
                    "subjectId": res.subjectId,
                    "grade": res.grade,
                    "marks": total_marks
                })

        average_marks = (total_score / count) if count > 0 else 0.0
        return {
            "average_marks": round(average_marks, 2),
            "failed_count": failed_count,
            "failed_subjects": fail_subjects
        }

    @staticmethod
    def calculate_performance_trends(data: Dict[str, Any]) -> Dict[str, Any]:
        """Determines if student grades are declining or improving semester-over-semester."""
        semester_results = data.get("results", [])
        if len(semester_results) < 2:
            return {"trend": "STABLE", "sgpa_drop": 0.0}

        latest = semester_results[-1]
        previous = semester_results[-2]

        drop = previous.sgpa - latest.sgpa
        if drop > 0.3:
            return {"trend": "DECLINING", "sgpa_drop": round(drop, 2)}
        elif drop < -0.3:
            return {"trend": "IMPROVING", "sgpa_drop": round(drop, 2)}
        return {"trend": "STABLE", "sgpa_drop": 0.0}

    @staticmethod
    def calculate_assignment_metrics(data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluates assignment submission counts and completion rates."""
        assignments = data.get("assignments", [])
        if not assignments:
            return {"completion_rate": 100.0, "pending_count": 0, "late_count": 0}

        total = len(assignments)
        completed = sum(1 for a in assignments if a.submissionStatus in ["SUBMITTED", "GRADED"])
        late = sum(1 for a in assignments if a.submissionStatus == "LATE")
        pending = sum(1 for a in assignments if a.submissionStatus == "PENDING")

        rate = (completed / total) * 100.0 if total > 0 else 100.0
        return {
            "completion_rate": round(rate, 2),
            "pending_count": pending,
            "late_count": late
        }

    @classmethod
    def calculate_risk_assessment(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates risk score (0-100) and advisory risk level."""
        completeness = cls.calculate_data_completeness(data)
        if completeness < 33.0:
            return {
                "score": 0.0,
                "level": "INSUFFICIENT_DATA",
                "completeness": completeness,
                "factors": [],
                "explanation": "Insufficient academic data available to generate a reliable risk score."
            }

        score = 0.0
        factors = []

        # 1. Attendance concern (max 40 pts)
        att_metrics = cls.calculate_attendance_metrics(data)
        rate = att_metrics["overall_rate"]
        att_contrib = 0.0
        if rate < 75.0:
            # 15 points minimum penalty plus linear scale up to 40
            att_contrib = 15.0 + ((75.0 - rate) * 1.25)
            att_contrib = min(att_contrib, 40.0)
            factors.append({
                "factorCode": "ATTENDANCE_CONCERN",
                "factorName": "Attendance rate concern",
                "observedValue": f"{rate}%",
                "normalizedValue": round(att_contrib / 40.0, 2),
                "weight": 40.0,
                "contribution": round(att_contrib, 2),
                "direction": "INCREASE",
                "explanation": f"Overall attendance rate of {rate}% is below the required 75% threshold.",
                "sourceType": "ATTENDANCE"
            })
        score += att_contrib

        # 2. Subject failures (max 50 pts)
        perf_metrics = cls.calculate_subject_performance(data)
        fail_count = perf_metrics["failed_count"]
        fail_contrib = 0.0
        if fail_count > 0:
            fail_contrib = min(fail_count * 20.0, 50.0)
            factors.append({
                "factorCode": "FAIL_CONCERN",
                "factorName": "Subject failure(s)",
                "observedValue": f"{fail_count} subject(s)",
                "normalizedValue": round(fail_contrib / 50.0, 2),
                "weight": 50.0,
                "contribution": round(fail_contrib, 2),
                "direction": "INCREASE",
                "explanation": f"Failing grades or marks below passing thresholds observed in {fail_count} subject(s).",
                "sourceType": "RESULT"
            })
        score += fail_contrib

        # 3. Assignment Incompletion (max 20 pts)
        ass_metrics = cls.calculate_assignment_metrics(data)
        ass_rate = ass_metrics["completion_rate"]
        ass_contrib = 0.0
        if ass_rate < 80.0:
            ass_contrib = (80.0 - ass_rate) * 0.5
            ass_contrib = min(ass_contrib, 20.0)
            factors.append({
                "factorCode": "ASSIGNMENT_INCOMPLETION",
                "factorName": "Assignment completion rate concern",
                "observedValue": f"{ass_rate}%",
                "normalizedValue": round(ass_contrib / 20.0, 2),
                "weight": 20.0,
                "contribution": round(ass_contrib, 2),
                "direction": "INCREASE",
                "explanation": f"Assignment completion rate of {ass_rate}% is below the 80% benchmark.",
                "sourceType": "ASSIGNMENT"
            })
        score += ass_contrib

        # 4. Performance Trend Decline (max 15 pts)
        trend_metrics = cls.calculate_performance_trends(data)
        trend_contrib = 0.0
        if trend_metrics["trend"] == "DECLINING":
            drop = trend_metrics["sgpa_drop"]
            trend_contrib = min(drop * 10.0, 15.0)
            factors.append({
                "factorCode": "PERFORMANCE_DECLINE",
                "factorName": "Semester performance decline",
                "observedValue": f"-{drop} SGPA",
                "normalizedValue": round(trend_contrib / 15.0, 2),
                "weight": 15.0,
                "contribution": round(trend_contrib, 2),
                "direction": "INCREASE",
                "explanation": f"Academic SGPA dropped by {drop} points compared to the previous semester.",
                "sourceType": "RESULT"
            })
        score += trend_contrib

        # Cap total score at 100
        final_score = min(round(score, 2), 100.0)

        # Risk level determination
        if final_score < 30.0:
            level = "LOW"
        elif final_score < 60.0:
            level = "MODERATE"
        elif final_score < 85.0:
            level = "HIGH"
        else:
            level = "CRITICAL"

        explanation = f"Student is evaluated as {level} risk with a score of {final_score}/100. "
        if level in ["HIGH", "CRITICAL"]:
            explanation += "This score indicates significant performance or attendance challenges. Immediate mentoring review is advised."
        elif level == "MODERATE":
            explanation += "This score indicates mild areas of concern that should be addressed before final exams."
        else:
            explanation += "This score indicates consistent academic performance and satisfactory attendance."

        return {
            "score": final_score,
            "level": level,
            "completeness": completeness,
            "factors": factors,
            "explanation": explanation
        }

    @classmethod
    def generate_explainable_insights(cls, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generates explainable insights (strengths, weaknesses, trends) based on deterministic checks."""
        insights = []

        # Attendance checks
        att_metrics = cls.calculate_attendance_metrics(data)
        rate = att_metrics["overall_rate"]
        if rate >= 95.0:
            insights.append({
                "type": "STRENGTH",
                "title": "Outstanding Class Attendance",
                "summary": f"Outstanding class attendance at {rate}%. Keep up the strong consistency!",
                "severity": "INFO"
            })
        elif rate < 75.0:
            insights.append({
                "type": "ATTENDANCE",
                "title": "Critical Attendance Deficit",
                "summary": f"Your overall attendance is {rate}%, which is below the minimum required 75%. Class presence is crucial for academic success.",
                "severity": "HIGH"
            })

        # Performance / Fail checks
        perf_metrics = cls.calculate_subject_performance(data)
        fail_count = perf_metrics["failed_count"]
        avg_marks = perf_metrics["average_marks"]

        if fail_count > 0:
            insights.append({
                "type": "WEAKNESS",
                "title": "Unresolved Failed Grade(s)",
                "summary": f"Failed grade(s) detected in {fail_count} subject(s). We recommend checking revaluation windows or booking a tutorial review.",
                "severity": "HIGH"
            })

        if avg_marks >= 85.0:
            insights.append({
                "type": "STRENGTH",
                "title": "High Average Marks",
                "summary": f"Excellent performance with average marks of {avg_marks}% across graded subjects.",
                "severity": "INFO"
            })

        # Trend checks
        trend_metrics = cls.calculate_performance_trends(data)
        if trend_metrics["trend"] == "DECLINING":
            insights.append({
                "type": "TREND",
                "title": "Decline in Semester Performance",
                "summary": f"Semester performance shows a decline. SGPA dropped by {trend_metrics['sgpa_drop']} compared to previous period.",
                "severity": "MEDIUM"
            })
        elif trend_metrics["trend"] == "IMPROVING":
            insights.append({
                "type": "TREND",
                "title": "Improvement in Semester Performance",
                "summary": f"Semester performance shows positive growth. SGPA improved by {-trend_metrics['sgpa_drop']} points.",
                "severity": "INFO"
            })

        # Assignment checks
        ass_metrics = cls.calculate_assignment_metrics(data)
        ass_rate = ass_metrics["completion_rate"]
        if ass_rate < 80.0:
            insights.append({
                "type": "DEADLINE",
                "title": "Assignment Submissions Lagging",
                "summary": f"Only {ass_rate}% of assignments have been submitted. You have {ass_metrics['pending_count']} pending assignments.",
                "severity": "MEDIUM"
            })

        return insights

    @classmethod
    def generate_recommendations(cls, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generates deterministic study and priority recommendations."""
        recommendations = []

        # 1. Attendance recommendation
        att_metrics = cls.calculate_attendance_metrics(data)
        if att_metrics["overall_rate"] < 75.0:
            recommendations.append({
                "category": "ATTENDANCE",
                "title": "Prioritize Class Attendance",
                "description": "Commit to attending all scheduled classes over the next 15 days. Regular presence will ensure eligibility for examinations and improve understanding.",
                "priority": "HIGH",
                "reason": f"Overall attendance ({att_metrics['overall_rate']}%) is below the regulatory 75% limit."
            })

        # 2. Subject support recommendation
        perf_metrics = cls.calculate_subject_performance(data)
        for fail in perf_metrics["failed_subjects"]:
            recommendations.append({
                "category": "SUBJECT_SUPPORT",
                "title": "Attend Faculty Remedial Sessions",
                "description": "Book a doubt-clearing session with your subject teacher or a peer tutor. Regular mock problem solving is advised.",
                "priority": "HIGH",
                "subjectId": fail["subjectId"],
                "reason": f"Failing grade detected. Subject marks computed as {fail['marks']}%."
            })

        # 3. Assignment backlog recommendation
        ass_metrics = cls.calculate_assignment_metrics(data)
        if ass_metrics["completion_rate"] < 80.0:
            recommendations.append({
                "category": "ASSIGNMENT",
                "title": "Submit Outstanding Assignments",
                "description": "List all your pending assignments, prioritize by due date, and submit them before the portal locks. Talk to faculty if extensions are needed.",
                "priority": "MEDIUM",
                "reason": f"Assignment completion rate is {ass_metrics['completion_rate']}%, indicating a queue of pending tasks."
            })

        return recommendations

    @classmethod
    def recalculate_student_intelligence(cls, db: Session, student_id: str, actor_id: Optional[str] = None) -> Dict[str, Any]:
        """Collects academic data, recalculates risk score, and generates insights/recommendations."""
        data = cls.collect_student_academic_data(db, student_id)
        if not data:
            return {"success": False, "message": "Student not found."}

        completeness = cls.calculate_data_completeness(data)
        assessment_data = cls.calculate_risk_assessment(data)

        # Get or create Profile
        profile = db.query(AcademicMentorProfile).filter_by(studentId=student_id).first()
        if not profile:
            profile = AcademicMentorProfile(
                studentId=student_id,
                engineType="LOCAL_EXPLAINABLE_ANALYTICS",
                dataCompleteness=completeness,
                currentRiskLevel=assessment_data["level"],
                currentRiskScore=assessment_data["score"],
                createdAt=datetime.utcnow()
            )
            db.add(profile)
        else:
            profile.dataCompleteness = completeness
            profile.currentRiskLevel = assessment_data["level"]
            profile.currentRiskScore = assessment_data["score"]
            profile.lastCalculatedAt = datetime.utcnow()

        db.commit()
        db.refresh(profile)

        # Version previous assessment records
        prev_assessments = db.query(AcademicRiskAssessment).filter_by(studentId=student_id).all()
        next_version = len(prev_assessments) + 1

        assessment = AcademicRiskAssessment(
            studentId=student_id,
            score=assessment_data["score"],
            level=assessment_data["level"],
            dataCompleteness=completeness,
            engineType="LOCAL_EXPLAINABLE_ANALYTICS",
            explanation=assessment_data["explanation"],
            assessedAt=datetime.utcnow(),
            version=next_version,
            createdAt=datetime.utcnow()
        )
        db.add(assessment)
        db.commit()
        db.refresh(assessment)

        # Write assessment factors
        for f in assessment_data["factors"]:
            factor = AcademicRiskFactor(
                assessmentId=assessment.id,
                factorCode=f["factorCode"],
                factorName=f["factorName"],
                observedValue=f["observedValue"],
                normalizedValue=f["normalizedValue"],
                weight=f["weight"],
                contribution=f["contribution"],
                direction=f["direction"],
                explanation=f["explanation"],
                sourceType=f["sourceType"]
            )
            db.add(factor)

        # Delete stale dismissed/expired insights and recommendations, generate new ones
        db.query(AcademicInsight).filter_by(studentId=student_id).delete()
        insights = cls.generate_explainable_insights(data)
        for ins in insights:
            insight = AcademicInsight(
                studentId=student_id,
                type=ins["type"],
                title=ins["title"],
                summary=ins["summary"],
                severity=ins["severity"],
                generatedBy="LOCAL_ANALYTICS_ENGINE",
                validFrom=datetime.utcnow(),
                createdAt=datetime.utcnow()
            )
            db.add(insight)

        # Handle Recommendations: Keep accepted/dismissed/completed recommendations, replace active/expired ones
        db.query(StudyRecommendation).filter(
            StudyRecommendation.studentId == student_id,
            StudyRecommendation.status.in_(["ACTIVE", "EXPIRED"])
        ).delete()

        recs = cls.generate_recommendations(data)
        for rec in recs:
            recommendation = StudyRecommendation(
                studentId=student_id,
                subjectId=rec.get("subjectId"),
                category=rec["category"],
                title=rec["title"],
                description=rec["description"],
                priority=rec["priority"],
                reason=rec["reason"],
                status="ACTIVE",
                generatedBy="LOCAL_ANALYTICS_ENGINE",
                createdAt=datetime.utcnow()
            )
            db.add(recommendation)

        db.commit()

        # Audit recalculation action
        cls.record_mentor_audit(
            db=db,
            action="RECALCULATE_INTELLIGENCE",
            entity_type="AcademicMentorProfile",
            entity_id=profile.id,
            actor_id=actor_id or student_id,
            student_id=student_id,
            metadata={"riskScore": assessment_data["score"], "riskLevel": assessment_data["level"]}
        )

        # Integrate notifications if risk level changes to HIGH or CRITICAL
        if assessment_data["level"] in ["HIGH", "CRITICAL"]:
            NotificationService.create_notification(
                db=db,
                recipient_id=student_id,
                title="Academic Advisory Notice",
                body=f"Your explainable academic risk has been assessed as {assessment_data['level']} ({assessment_data['score']}/100). Please review your recommendations and study plans.",
                type="ADVISORY",
                priority="HIGH",
                channel="IN_APP",
                category="ACADEMIC"
            )

        return {
            "success": True,
            "profile": profile,
            "assessment": assessment,
            "insights_count": len(insights),
            "recommendations_count": len(recs)
        }
