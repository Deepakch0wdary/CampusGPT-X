from fastapi import APIRouter
from app.api.v1.endpoints import health, auth, users, sessions, audits, academics, students, faculties

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["System Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["Sessions"])
api_router.include_router(audits.router, prefix="/audits", tags=["Audits"])

# Student Portal Router
api_router.include_router(students.router, prefix="/student", tags=["Student Portal"])

# Faculty Portal Router
api_router.include_router(faculties.router, prefix="/faculty", tags=["Faculty Portal"])

# Academic Structure Routers
api_router.include_router(academics.academic_years_router, prefix="/academic-years", tags=["Academic Years"])
api_router.include_router(academics.departments_router, prefix="/departments", tags=["Departments"])
api_router.include_router(academics.programs_router, prefix="/programs", tags=["Programs"])
api_router.include_router(academics.courses_router, prefix="/courses", tags=["Courses"])
api_router.include_router(academics.semesters_router, prefix="/semesters", tags=["Semesters"])
api_router.include_router(academics.subjects_router, prefix="/subjects", tags=["Subjects"])
api_router.include_router(academics.sections_router, prefix="/sections", tags=["Sections"])
api_router.include_router(academics.buildings_router, prefix="/buildings", tags=["Buildings"])
api_router.include_router(academics.rooms_router, prefix="/rooms", tags=["Rooms"])
api_router.include_router(academics.laboratories_router, prefix="/laboratories", tags=["Laboratories"])
api_router.include_router(academics.faculty_assignments_router, prefix="/faculty-assignments", tags=["Faculty Assignments"])
