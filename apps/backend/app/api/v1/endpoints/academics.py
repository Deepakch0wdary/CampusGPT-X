import uuid
import openpyxl
from io import BytesIO
from datetime import datetime
from typing import Optional, List, Union
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc

from app.core.dependencies import get_db
from app.core.rbac_middleware import PermissionChecker
from app.core.auth_middleware import get_current_user_no_password_force
from app.core.responses import make_response
from app.models.models import (
    User, Role, Department, Section, AcademicYear, Program, Course,
    Semester, Subject, Building, Room, Laboratory, FacultyAssignment, AuditLog
)

# -------------------------------------------------------------
# PYDANTIC SCHEMAS
# -------------------------------------------------------------

class AcademicYearSchema(BaseModel):
    name: str
    startDate: str
    endDate: str
    status: Optional[str] = "ACTIVE"
    currentAcademicYear: Optional[bool] = False

class DepartmentSchema(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    deanHod: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    building: Optional[str] = None
    status: Optional[str] = "ACTIVE"

class ProgramSchema(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    departmentId: str

class CourseSchema(BaseModel):
    code: str
    name: str
    credits: int
    duration: str
    departmentId: str
    programId: str
    description: Optional[str] = None
    status: Optional[str] = "ACTIVE"

class SemesterSchema(BaseModel):
    semesterNumber: int
    academicYearId: str
    programId: str
    startDate: str
    endDate: str
    currentSemester: Optional[bool] = False

class SubjectSchema(BaseModel):
    code: str
    name: str
    credits: int
    theoryHours: Optional[int] = 0
    labHours: Optional[int] = 0
    elective: Optional[bool] = False
    mandatory: Optional[bool] = True
    departmentId: str
    semesterId: str
    courseId: str

class SectionSchema(BaseModel):
    name: str
    capacity: int
    semesterId: str
    departmentId: str
    programId: str
    facultyAdvisorId: Optional[str] = None
    academicYearId: Optional[str] = None

class BuildingSchema(BaseModel):
    name: str
    code: str
    floors: int
    description: Optional[str] = None

class RoomSchema(BaseModel):
    roomNumber: str
    roomType: Optional[str] = "CLASSROOM"
    capacity: int
    buildingId: str
    floor: int
    projector: Optional[bool] = False
    smartBoard: Optional[bool] = False
    airConditioning: Optional[bool] = False
    status: Optional[str] = "ACTIVE"
    departmentId: Optional[str] = None

class LaboratorySchema(BaseModel):
    labName: str
    departmentId: str
    capacity: int
    systems: Optional[int] = 0
    software: Optional[str] = None
    labAssistant: Optional[str] = None

class FacultyAssignmentSchema(BaseModel):
    departmentId: str
    subjectId: str
    facultyId: str
    sectionId: str
    semesterId: str
    academicYearId: str

# -------------------------------------------------------------
# HELPER PARSERS
# -------------------------------------------------------------
def parse_date(date_str: str) -> datetime:
    try:
        return datetime.strptime(date_str.split('T')[0], "%Y-%m-%d")
    except Exception:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {date_str}. Use YYYY-MM-DD.")

def log_audit(db: Session, user_id: str, action: str, details: str):
    audit = AuditLog(
        id=str(uuid.uuid4()),
        userId=user_id,
        action=action,
        details=details
    )
    db.add(audit)
    db.commit()

# -------------------------------------------------------------
# 1. ACADEMIC YEAR ROUTER
# -------------------------------------------------------------
academic_years_router = APIRouter()

@academic_years_router.post("")
def create_academic_year(payload: AcademicYearSchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    existing = db.query(AcademicYear).filter_by(name=payload.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Academic Year name already exists.")
    
    start_dt = parse_date(payload.startDate)
    end_dt = parse_date(payload.endDate)
    if start_dt >= end_dt:
        raise HTTPException(status_code=400, detail="Start Date must be before End Date.")

    if payload.currentAcademicYear:
        db.query(AcademicYear).update({AcademicYear.currentAcademicYear: False})

    ay = AcademicYear(
        id=str(uuid.uuid4()),
        name=payload.name,
        startDate=start_dt,
        endDate=end_dt,
        status=payload.status,
        currentAcademicYear=payload.currentAcademicYear
    )
    db.add(ay)
    db.commit()
    db.refresh(ay)
    log_audit(db, current_user.id, "ACADEMIC_YEAR_CREATE", f"Created academic year {ay.name}.")
    
    res = {"id": ay.id, "name": ay.name}
    return make_response(success=True, message="Academic Year created successfully.", data=res, extra_compat=res)

@academic_years_router.get("")
def list_academic_years(search: Optional[str] = None, page: int = 1, limit: int = 10, db: Session = Depends(get_db)):
    query = db.query(AcademicYear)
    if search:
        query = query.filter(AcademicYear.name.ilike(f"%{search}%"))
    
    total = query.count()
    items = query.offset((page - 1) * limit).limit(limit).all()
    
    data = [{
        "id": x.id, "name": x.name, "startDate": x.startDate, "endDate": x.endDate,
        "status": x.status, "currentAcademicYear": x.currentAcademicYear
    } for x in items]
    
    res = {"academic_years": data, "total": total, "page": page, "pages": (total + limit - 1) // limit}
    return make_response(success=True, message="Academic Years retrieved.", data=res, extra_compat=res)

@academic_years_router.get("/{id}")
def get_academic_year(id: str, db: Session = Depends(get_db)):
    ay = db.query(AcademicYear).filter_by(id=id).first()
    if not ay:
        raise HTTPException(status_code=404, detail="Academic Year not found.")
    res = {
        "id": ay.id, "name": ay.name, "startDate": ay.startDate, "endDate": ay.endDate,
        "status": ay.status, "currentAcademicYear": ay.currentAcademicYear
    }
    return make_response(success=True, message="Academic Year found.", data=res, extra_compat=res)

@academic_years_router.put("/{id}")
def update_academic_year(id: str, payload: AcademicYearSchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    ay = db.query(AcademicYear).filter_by(id=id).first()
    if not ay:
        raise HTTPException(status_code=404, detail="Academic Year not found.")
    
    start_dt = parse_date(payload.startDate)
    end_dt = parse_date(payload.endDate)
    if start_dt >= end_dt:
        raise HTTPException(status_code=400, detail="Start Date must be before End Date.")

    if payload.currentAcademicYear:
        db.query(AcademicYear).filter(AcademicYear.id != id).update({AcademicYear.currentAcademicYear: False})

    ay.name = payload.name
    ay.startDate = start_dt
    ay.endDate = end_dt
    ay.status = payload.status
    ay.currentAcademicYear = payload.currentAcademicYear
    db.commit()
    log_audit(db, current_user.id, "ACADEMIC_YEAR_UPDATE", f"Updated academic year {ay.name}.")
    return make_response(success=True, message="Academic Year updated.", data={})

@academic_years_router.delete("/{id}")
def delete_academic_year(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    ay = db.query(AcademicYear).filter_by(id=id).first()
    if not ay:
        raise HTTPException(status_code=404, detail="Academic Year not found.")
    db.delete(ay)
    db.commit()
    log_audit(db, current_user.id, "ACADEMIC_YEAR_DELETE", f"Deleted academic year {ay.name}.")
    return make_response(success=True, message="Academic Year deleted.", data={})

# -------------------------------------------------------------
# 2. DEPARTMENT ROUTER
# -------------------------------------------------------------
departments_router = APIRouter()

@departments_router.post("")
def create_department(payload: DepartmentSchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    existing = db.query(Department).filter(or_(Department.name == payload.name, Department.code == payload.code)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Department Name or Code already exists.")
    
    dept = Department(
        id=str(uuid.uuid4()),
        name=payload.name,
        code=payload.code,
        description=payload.description,
        deanHod=payload.deanHod,
        email=payload.email,
        phone=payload.phone,
        building=payload.building,
        status=payload.status
    )
    db.add(dept)
    db.commit()
    db.refresh(dept)
    log_audit(db, current_user.id, "DEPARTMENT_CREATE", f"Created department {dept.name} ({dept.code}).")
    res = {"id": dept.id, "name": dept.name, "code": dept.code}
    return make_response(success=True, message="Department created successfully.", data=res, extra_compat=res)

@departments_router.get("")
def list_departments(search: Optional[str] = None, page: int = 1, limit: int = 10, db: Session = Depends(get_db)):
    query = db.query(Department)
    if search:
        query = query.filter(or_(Department.name.ilike(f"%{search}%"), Department.code.ilike(f"%{search}%")))
    
    total = query.count()
    items = query.offset((page - 1) * limit).limit(limit).all()
    
    data = [{
        "id": x.id, "name": x.name, "code": x.code, "description": x.description,
        "deanHod": x.deanHod, "email": x.email, "phone": x.phone, "building": x.building, "status": x.status
    } for x in items]
    
    res = {"departments": data, "total": total, "page": page, "pages": (total + limit - 1) // limit}
    return make_response(success=True, message="Departments list retrieved.", data=res, extra_compat=res)

@departments_router.get("/{id}")
def get_department(id: str, db: Session = Depends(get_db)):
    dept = db.query(Department).filter_by(id=id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found.")
    res = {
        "id": dept.id, "name": dept.name, "code": dept.code, "description": dept.description,
        "deanHod": dept.deanHod, "email": dept.email, "phone": dept.phone, "building": dept.building, "status": dept.status
    }
    return make_response(success=True, message="Department found.", data=res, extra_compat=res)

@departments_router.put("/{id}")
def update_department(id: str, payload: DepartmentSchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    dept = db.query(Department).filter_by(id=id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found.")
    
    existing = db.query(Department).filter(Department.id != id).filter(or_(Department.name == payload.name, Department.code == payload.code)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Department Name or Code already exists.")
    
    dept.name = payload.name
    dept.code = payload.code
    dept.description = payload.description
    dept.deanHod = payload.deanHod
    dept.email = payload.email
    dept.phone = payload.phone
    dept.building = payload.building
    dept.status = payload.status
    db.commit()
    log_audit(db, current_user.id, "DEPARTMENT_UPDATE", f"Updated department {dept.name}.")
    return make_response(success=True, message="Department updated.", data={})

@departments_router.delete("/{id}")
def delete_department(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    dept = db.query(Department).filter_by(id=id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found.")
    
    if len(dept.courses) > 0:
        raise HTTPException(status_code=400, detail="Cannot delete department with active courses.")
        
    db.delete(dept)
    db.commit()
    log_audit(db, current_user.id, "DEPARTMENT_DELETE", f"Deleted department {dept.name}.")
    return make_response(success=True, message="Department deleted.", data={})

# -------------------------------------------------------------
# 3. PROGRAM ROUTER
# -------------------------------------------------------------
programs_router = APIRouter()

@programs_router.post("")
def create_program(payload: ProgramSchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    existing = db.query(Program).filter(or_(Program.name == payload.name, Program.code == payload.code)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Program Name or Code already exists.")
    
    prog = Program(
        id=str(uuid.uuid4()),
        name=payload.name,
        code=payload.code,
        description=payload.description,
        departmentId=payload.departmentId
    )
    db.add(prog)
    db.commit()
    db.refresh(prog)
    log_audit(db, current_user.id, "PROGRAM_CREATE", f"Created program {prog.name}.")
    res = {"id": prog.id, "name": prog.name}
    return make_response(success=True, message="Program created successfully.", data=res, extra_compat=res)

@programs_router.get("")
def list_programs(search: Optional[str] = None, departmentId: Optional[str] = None, page: int = 1, limit: int = 10, db: Session = Depends(get_db)):
    query = db.query(Program)
    if departmentId:
        query = query.filter_by(departmentId=departmentId)
    if search:
        query = query.filter(or_(Program.name.ilike(f"%{search}%"), Program.code.ilike(f"%{search}%")))
    
    total = query.count()
    items = query.offset((page - 1) * limit).limit(limit).all()
    
    data = [{
        "id": x.id, "name": x.name, "code": x.code, "description": x.description,
        "departmentId": x.departmentId, "departmentName": x.department.name if x.department else None
    } for x in items]
    
    res = {"programs": data, "total": total, "page": page, "pages": (total + limit - 1) // limit}
    return make_response(success=True, message="Programs list retrieved.", data=res, extra_compat=res)

@programs_router.get("/{id}")
def get_program(id: str, db: Session = Depends(get_db)):
    prog = db.query(Program).filter_by(id=id).first()
    if not prog:
        raise HTTPException(status_code=404, detail="Program not found.")
    res = {
        "id": prog.id, "name": prog.name, "code": prog.code, "description": prog.description, "departmentId": prog.departmentId
    }
    return make_response(success=True, message="Program found.", data=res, extra_compat=res)

@programs_router.put("/{id}")
def update_program(id: str, payload: ProgramSchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    prog = db.query(Program).filter_by(id=id).first()
    if not prog:
        raise HTTPException(status_code=404, detail="Program not found.")
    
    existing = db.query(Program).filter(Program.id != id).filter(or_(Program.name == payload.name, Program.code == payload.code)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Program Name or Code already exists.")
    
    prog.name = payload.name
    prog.code = payload.code
    prog.description = payload.description
    prog.departmentId = payload.departmentId
    db.commit()
    log_audit(db, current_user.id, "PROGRAM_UPDATE", f"Updated program {prog.name}.")
    return make_response(success=True, message="Program updated.", data={})

@programs_router.delete("/{id}")
def delete_program(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    prog = db.query(Program).filter_by(id=id).first()
    if not prog:
        raise HTTPException(status_code=404, detail="Program not found.")
    db.delete(prog)
    db.commit()
    log_audit(db, current_user.id, "PROGRAM_DELETE", f"Deleted program {prog.name}.")
    return make_response(success=True, message="Program deleted.", data={})

# -------------------------------------------------------------
# 4. COURSE ROUTER
# -------------------------------------------------------------
courses_router = APIRouter()

@courses_router.post("")
def create_course(payload: CourseSchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    existing = db.query(Course).filter_by(code=payload.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Course Code already exists.")
    
    course = Course(
        id=str(uuid.uuid4()),
        code=payload.code,
        name=payload.name,
        credits=payload.credits,
        duration=payload.duration,
        departmentId=payload.departmentId,
        programId=payload.programId,
        description=payload.description,
        status=payload.status
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    log_audit(db, current_user.id, "COURSE_CREATE", f"Created course {course.name} ({course.code}).")
    res = {"id": course.id, "name": course.name}
    return make_response(success=True, message="Course created successfully.", data=res, extra_compat=res)

@courses_router.get("")
def list_courses(search: Optional[str] = None, departmentId: Optional[str] = None, page: int = 1, limit: int = 10, db: Session = Depends(get_db)):
    query = db.query(Course)
    if departmentId:
        query = query.filter_by(departmentId=departmentId)
    if search:
        query = query.filter(or_(Course.name.ilike(f"%{search}%"), Course.code.ilike(f"%{search}%")))
    
    total = query.count()
    items = query.offset((page - 1) * limit).limit(limit).all()
    
    data = [{
        "id": x.id, "code": x.code, "name": x.name, "credits": x.credits, "duration": x.duration,
        "departmentId": x.departmentId, "departmentName": x.department.name if x.department else None,
        "programId": x.programId, "programName": x.program.name if x.program else None,
        "description": x.description, "status": x.status
    } for x in items]
    
    res = {"courses": data, "total": total, "page": page, "pages": (total + limit - 1) // limit}
    return make_response(success=True, message="Courses list retrieved.", data=res, extra_compat=res)

@courses_router.get("/{id}")
def get_course(id: str, db: Session = Depends(get_db)):
    course = db.query(Course).filter_by(id=id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")
    res = {
        "id": course.id, "code": course.code, "name": course.name, "credits": course.credits, "duration": course.duration,
        "departmentId": course.departmentId, "programId": course.programId, "description": course.description, "status": course.status
    }
    return make_response(success=True, message="Course found.", data=res, extra_compat=res)

@courses_router.put("/{id}")
def update_course(id: str, payload: CourseSchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    course = db.query(Course).filter_by(id=id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")
    
    existing = db.query(Course).filter(Course.id != id).filter_by(code=payload.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Course Code already exists.")
    
    course.name = payload.name
    course.code = payload.code
    course.credits = payload.credits
    course.duration = payload.duration
    course.departmentId = payload.departmentId
    course.programId = payload.programId
    course.description = payload.description
    course.status = payload.status
    db.commit()
    log_audit(db, current_user.id, "COURSE_UPDATE", f"Updated course {course.name}.")
    return make_response(success=True, message="Course updated.", data={})

@courses_router.delete("/{id}")
def delete_course(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    course = db.query(Course).filter_by(id=id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")
    db.delete(course)
    db.commit()
    log_audit(db, current_user.id, "COURSE_DELETE", f"Deleted course {course.name}.")
    return make_response(success=True, message="Course deleted.", data={})

# -------------------------------------------------------------
# 5. SEMESTER ROUTER
# -------------------------------------------------------------
semesters_router = APIRouter()

@semesters_router.post("")
def create_semester(payload: SemesterSchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    start_dt = parse_date(payload.startDate)
    end_dt = parse_date(payload.endDate)
    if start_dt >= end_dt:
        raise HTTPException(status_code=400, detail="Start Date must be before End Date.")
        
    # Validation: Only one semester can be current for a program/academic year
    if payload.currentSemester:
        db.query(Semester).filter_by(programId=payload.programId, academicYearId=payload.academicYearId).update({Semester.currentSemester: False})

    sem = Semester(
        id=str(uuid.uuid4()),
        semesterNumber=payload.semesterNumber,
        academicYearId=payload.academicYearId,
        programId=payload.programId,
        startDate=start_dt,
        endDate=end_dt,
        currentSemester=payload.currentSemester
    )
    db.add(sem)
    db.commit()
    db.refresh(sem)
    log_audit(db, current_user.id, "SEMESTER_CREATE", f"Created semester {sem.semesterNumber} for program {sem.programId}.")
    res = {"id": sem.id, "semesterNumber": sem.semesterNumber}
    return make_response(success=True, message="Semester created successfully.", data=res, extra_compat=res)

@semesters_router.get("")
def list_semesters(programId: Optional[str] = None, page: int = 1, limit: int = 10, db: Session = Depends(get_db)):
    query = db.query(Semester)
    if programId:
        query = query.filter_by(programId=programId)
    
    total = query.count()
    items = query.offset((page - 1) * limit).limit(limit).all()
    
    data = [{
        "id": x.id, "semesterNumber": x.semesterNumber,
        "academicYearId": x.academicYearId, "academicYearName": x.academicYear.name if x.academicYear else None,
        "programId": x.programId, "programName": x.program.name if x.program else None,
        "startDate": x.startDate, "endDate": x.endDate, "currentSemester": x.currentSemester
    } for x in items]
    
    res = {"semesters": data, "total": total, "page": page, "pages": (total + limit - 1) // limit}
    return make_response(success=True, message="Semesters list retrieved.", data=res, extra_compat=res)

@semesters_router.get("/{id}")
def get_semester(id: str, db: Session = Depends(get_db)):
    sem = db.query(Semester).filter_by(id=id).first()
    if not sem:
        raise HTTPException(status_code=404, detail="Semester not found.")
    res = {
        "id": sem.id, "semesterNumber": sem.semesterNumber, "academicYearId": sem.academicYearId,
        "programId": sem.programId, "startDate": sem.startDate, "endDate": sem.endDate, "currentSemester": sem.currentSemester
    }
    return make_response(success=True, message="Semester found.", data=res, extra_compat=res)

@semesters_router.put("/{id}")
def update_semester(id: str, payload: SemesterSchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    sem = db.query(Semester).filter_by(id=id).first()
    if not sem:
        raise HTTPException(status_code=404, detail="Semester not found.")
    
    start_dt = parse_date(payload.startDate)
    end_dt = parse_date(payload.endDate)
    if start_dt >= end_dt:
        raise HTTPException(status_code=400, detail="Start Date must be before End Date.")
        
    if payload.currentSemester:
        db.query(Semester).filter(Semester.id != id).filter_by(programId=payload.programId, academicYearId=payload.academicYearId).update({Semester.currentSemester: False})

    sem.semesterNumber = payload.semesterNumber
    sem.academicYearId = payload.academicYearId
    sem.programId = payload.programId
    sem.startDate = start_dt
    sem.endDate = end_dt
    sem.currentSemester = payload.currentSemester
    db.commit()
    log_audit(db, current_user.id, "SEMESTER_UPDATE", f"Updated semester {sem.semesterNumber}.")
    return make_response(success=True, message="Semester updated.", data={})

@semesters_router.delete("/{id}")
def delete_semester(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    sem = db.query(Semester).filter_by(id=id).first()
    if not sem:
        raise HTTPException(status_code=404, detail="Semester not found.")
    db.delete(sem)
    db.commit()
    log_audit(db, current_user.id, "SEMESTER_DELETE", f"Deleted semester {sem.semesterNumber}.")
    return make_response(success=True, message="Semester deleted.", data={})

# -------------------------------------------------------------
# 6. SUBJECT ROUTER
# -------------------------------------------------------------
subjects_router = APIRouter()

@subjects_router.post("")
def create_subject(payload: SubjectSchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    existing = db.query(Subject).filter_by(code=payload.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Subject Code already exists.")
    
    subj = Subject(
        id=str(uuid.uuid4()),
        code=payload.code,
        name=payload.name,
        credits=payload.credits,
        theoryHours=payload.theoryHours,
        labHours=payload.labHours,
        elective=payload.elective,
        mandatory=payload.mandatory,
        departmentId=payload.departmentId,
        semesterId=payload.semesterId,
        courseId=payload.courseId
    )
    db.add(subj)
    db.commit()
    db.refresh(subj)
    log_audit(db, current_user.id, "SUBJECT_CREATE", f"Created subject {subj.name} ({subj.code}).")
    res = {"id": subj.id, "name": subj.name}
    return make_response(success=True, message="Subject created successfully.", data=res, extra_compat=res)

@subjects_router.get("")
def list_subjects(search: Optional[str] = None, departmentId: Optional[str] = None, page: int = 1, limit: int = 10, db: Session = Depends(get_db)):
    query = db.query(Subject)
    if departmentId:
        query = query.filter_by(departmentId=departmentId)
    if search:
        query = query.filter(or_(Subject.name.ilike(f"%{search}%"), Subject.code.ilike(f"%{search}%")))
    
    total = query.count()
    items = query.offset((page - 1) * limit).limit(limit).all()
    
    data = [{
        "id": x.id, "code": x.code, "name": x.name, "credits": x.credits,
        "theoryHours": x.theoryHours, "labHours": x.labHours, "elective": x.elective, "mandatory": x.mandatory,
        "departmentId": x.departmentId, "departmentName": x.department.name if x.department else None,
        "semesterId": x.semesterId, "semesterNumber": x.semester.semesterNumber if x.semester else None,
        "courseId": x.courseId, "courseName": x.course.name if x.course else None
    } for x in items]
    
    res = {"subjects": data, "total": total, "page": page, "pages": (total + limit - 1) // limit}
    return make_response(success=True, message="Subjects list retrieved.", data=res, extra_compat=res)

@subjects_router.get("/{id}")
def get_subject(id: str, db: Session = Depends(get_db)):
    subj = db.query(Subject).filter_by(id=id).first()
    if not subj:
        raise HTTPException(status_code=404, detail="Subject not found.")
    res = {
        "id": subj.id, "code": subj.code, "name": subj.name, "credits": subj.credits,
        "theoryHours": subj.theoryHours, "labHours": subj.labHours, "elective": subj.elective, "mandatory": subj.mandatory,
        "departmentId": subj.departmentId, "semesterId": subj.semesterId, "courseId": subj.courseId
    }
    return make_response(success=True, message="Subject found.", data=res, extra_compat=res)

@subjects_router.put("/{id}")
def update_subject(id: str, payload: SubjectSchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    subj = db.query(Subject).filter_by(id=id).first()
    if not subj:
        raise HTTPException(status_code=404, detail="Subject not found.")
    
    existing = db.query(Subject).filter(Subject.id != id).filter_by(code=payload.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Subject Code already exists.")
    
    subj.name = payload.name
    subj.code = payload.code
    subj.credits = payload.credits
    subj.theoryHours = payload.theoryHours
    subj.labHours = payload.labHours
    subj.elective = payload.elective
    subj.mandatory = payload.mandatory
    subj.departmentId = payload.departmentId
    subj.semesterId = payload.semesterId
    subj.courseId = payload.courseId
    db.commit()
    log_audit(db, current_user.id, "SUBJECT_UPDATE", f"Updated subject {subj.name}.")
    return make_response(success=True, message="Subject updated.", data={})

@subjects_router.delete("/{id}")
def delete_subject(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    subj = db.query(Subject).filter_by(id=id).first()
    if not subj:
        raise HTTPException(status_code=404, detail="Subject not found.")
    
    # Check if subject linked to active assignments
    if len(subj.facultyAssignments) > 0:
        raise HTTPException(status_code=400, detail="Cannot delete subject linked to active assignments.")
        
    db.delete(subj)
    db.commit()
    log_audit(db, current_user.id, "SUBJECT_DELETE", f"Deleted subject {subj.name}.")
    return make_response(success=True, message="Subject deleted.", data={})

# -------------------------------------------------------------
# 7. SECTION ROUTER
# -------------------------------------------------------------
sections_router = APIRouter()

@sections_router.post("")
def create_section(payload: SectionSchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    if payload.facultyAdvisorId:
        advisor = db.query(User).filter_by(id=payload.facultyAdvisorId).first()
        if not advisor or advisor.role.name != "TEACHER":
            raise HTTPException(status_code=400, detail="Faculty advisor must be a designated Teacher.")

    sect = Section(
        id=str(uuid.uuid4()),
        name=payload.name,
        capacity=payload.capacity,
        semesterId=payload.semesterId,
        departmentId=payload.departmentId,
        programId=payload.programId,
        facultyAdvisorId=payload.facultyAdvisorId,
        academicYearId=payload.academicYearId
    )
    db.add(sect)
    db.commit()
    db.refresh(sect)
    log_audit(db, current_user.id, "SECTION_CREATE", f"Created section {sect.name}.")
    res = {"id": sect.id, "name": sect.name}
    return make_response(success=True, message="Section created successfully.", data=res, extra_compat=res)

@sections_router.get("")
def list_sections(search: Optional[str] = None, departmentId: Optional[str] = None, page: int = 1, limit: int = 10, db: Session = Depends(get_db)):
    query = db.query(Section)
    if departmentId:
        query = query.filter_by(departmentId=departmentId)
    if search:
        query = query.filter(Section.name.ilike(f"%{search}%"))
    
    total = query.count()
    items = query.offset((page - 1) * limit).limit(limit).all()
    
    data = [{
        "id": x.id, "name": x.name, "capacity": x.capacity,
        "semesterId": x.semesterId, "semesterNumber": x.semester.semesterNumber if x.semester else None,
        "departmentId": x.departmentId, "departmentName": x.department.name if x.department else None,
        "programId": x.programId, "programName": x.program.name if x.program else None,
        "facultyAdvisorId": x.facultyAdvisorId, "facultyAdvisorName": x.facultyAdvisor.name if x.facultyAdvisor else None,
        "academicYearId": x.academicYearId, "academicYearName": x.academicYear.name if x.academicYear else None
    } for x in items]
    
    res = {"sections": data, "total": total, "page": page, "pages": (total + limit - 1) // limit}
    return make_response(success=True, message="Sections list retrieved.", data=res, extra_compat=res)

@sections_router.get("/{id}")
def get_section(id: str, db: Session = Depends(get_db)):
    sect = db.query(Section).filter_by(id=id).first()
    if not sect:
        raise HTTPException(status_code=404, detail="Section not found.")
    res = {
        "id": sect.id, "name": sect.name, "capacity": sect.capacity, "semesterId": sect.semesterId,
        "departmentId": sect.departmentId, "programId": sect.programId, "facultyAdvisorId": sect.facultyAdvisorId, "academicYearId": sect.academicYearId
    }
    return make_response(success=True, message="Section found.", data=res, extra_compat=res)

@sections_router.put("/{id}")
def update_section(id: str, payload: SectionSchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    sect = db.query(Section).filter_by(id=id).first()
    if not sect:
        raise HTTPException(status_code=404, detail="Section not found.")
    
    if payload.facultyAdvisorId:
        advisor = db.query(User).filter_by(id=payload.facultyAdvisorId).first()
        if not advisor or advisor.role.name != "TEACHER":
            raise HTTPException(status_code=400, detail="Faculty advisor must be a designated Teacher.")

    sect.name = payload.name
    sect.capacity = payload.capacity
    sect.semesterId = payload.semesterId
    sect.departmentId = payload.departmentId
    sect.programId = payload.programId
    sect.facultyAdvisorId = payload.facultyAdvisorId
    sect.academicYearId = payload.academicYearId
    db.commit()
    log_audit(db, current_user.id, "SECTION_UPDATE", f"Updated section {sect.name}.")
    return make_response(success=True, message="Section updated.", data={})

@sections_router.delete("/{id}")
def delete_section(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    sect = db.query(Section).filter_by(id=id).first()
    if not sect:
        raise HTTPException(status_code=404, detail="Section not found.")
    db.delete(sect)
    db.commit()
    log_audit(db, current_user.id, "SECTION_DELETE", f"Deleted section {sect.name}.")
    return make_response(success=True, message="Section deleted.", data={})

# -------------------------------------------------------------
# 8. BUILDING ROUTER
# -------------------------------------------------------------
buildings_router = APIRouter()

@buildings_router.post("")
def create_building(payload: BuildingSchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    existing = db.query(Building).filter(or_(Building.name == payload.name, Building.code == payload.code)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Building Name or Code already exists.")
    
    bld = Building(
        id=str(uuid.uuid4()),
        name=payload.name,
        code=payload.code,
        floors=payload.floors,
        description=payload.description
    )
    db.add(bld)
    db.commit()
    db.refresh(bld)
    log_audit(db, current_user.id, "BUILDING_CREATE", f"Created building {bld.name}.")
    res = {"id": bld.id, "name": bld.name}
    return make_response(success=True, message="Building created successfully.", data=res, extra_compat=res)

@buildings_router.get("")
def list_buildings(search: Optional[str] = None, page: int = 1, limit: int = 10, db: Session = Depends(get_db)):
    query = db.query(Building)
    if search:
        query = query.filter(or_(Building.name.ilike(f"%{search}%"), Building.code.ilike(f"%{search}%")))
    
    total = query.count()
    items = query.offset((page - 1) * limit).limit(limit).all()
    
    data = [{
        "id": x.id, "name": x.name, "code": x.code, "floors": x.floors, "description": x.description
    } for x in items]
    
    res = {"buildings": data, "total": total, "page": page, "pages": (total + limit - 1) // limit}
    return make_response(success=True, message="Buildings list retrieved.", data=res, extra_compat=res)

@buildings_router.get("/{id}")
def get_building(id: str, db: Session = Depends(get_db)):
    bld = db.query(Building).filter_by(id=id).first()
    if not bld:
        raise HTTPException(status_code=404, detail="Building not found.")
    res = {
        "id": bld.id, "name": bld.name, "code": bld.code, "floors": bld.floors, "description": bld.description
    }
    return make_response(success=True, message="Building found.", data=res, extra_compat=res)

@buildings_router.put("/{id}")
def update_building(id: str, payload: BuildingSchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    bld = db.query(Building).filter_by(id=id).first()
    if not bld:
        raise HTTPException(status_code=404, detail="Building not found.")
    
    existing = db.query(Building).filter(Building.id != id).filter(or_(Building.name == payload.name, Building.code == payload.code)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Building Name or Code already exists.")
    
    bld.name = payload.name
    bld.code = payload.code
    bld.floors = payload.floors
    bld.description = payload.description
    db.commit()
    log_audit(db, current_user.id, "BUILDING_UPDATE", f"Updated building {bld.name}.")
    return make_response(success=True, message="Building updated.", data={})

@buildings_router.delete("/{id}")
def delete_building(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    bld = db.query(Building).filter_by(id=id).first()
    if not bld:
        raise HTTPException(status_code=404, detail="Building not found.")
    db.delete(bld)
    db.commit()
    log_audit(db, current_user.id, "BUILDING_DELETE", f"Deleted building {bld.name}.")
    return make_response(success=True, message="Building deleted.", data={})

# -------------------------------------------------------------
# 9. ROOM ROUTER
# -------------------------------------------------------------
rooms_router = APIRouter()

@rooms_router.post("")
def create_room(payload: RoomSchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    existing = db.query(Room).filter_by(roomNumber=payload.roomNumber).first()
    if existing:
        raise HTTPException(status_code=400, detail="Room Number already exists.")
    
    room = Room(
        id=str(uuid.uuid4()),
        roomNumber=payload.roomNumber,
        roomType=payload.roomType,
        capacity=payload.capacity,
        buildingId=payload.buildingId,
        floor=payload.floor,
        projector=payload.projector,
        smartBoard=payload.smartBoard,
        airConditioning=payload.airConditioning,
        status=payload.status,
        departmentId=payload.departmentId
    )
    db.add(room)
    db.commit()
    db.refresh(room)
    log_audit(db, current_user.id, "ROOM_CREATE", f"Created room {room.roomNumber}.")
    res = {"id": room.id, "roomNumber": room.roomNumber}
    return make_response(success=True, message="Room created successfully.", data=res, extra_compat=res)

@rooms_router.get("")
def list_rooms(search: Optional[str] = None, buildingId: Optional[str] = None, page: int = 1, limit: int = 10, db: Session = Depends(get_db)):
    query = db.query(Room)
    if buildingId:
        query = query.filter_by(buildingId=buildingId)
    if search:
        query = query.filter(Room.roomNumber.ilike(f"%{search}%"))
    
    total = query.count()
    items = query.offset((page - 1) * limit).limit(limit).all()
    
    data = [{
        "id": x.id, "roomNumber": x.roomNumber, "roomType": x.roomType, "capacity": x.capacity,
        "buildingId": x.buildingId, "buildingName": x.building.name if x.building else None,
        "floor": x.floor, "projector": x.projector, "smartBoard": x.smartBoard, "airConditioning": x.airConditioning,
        "status": x.status, "departmentId": x.departmentId, "departmentName": x.department.name if x.department else None
    } for x in items]
    
    res = {"rooms": data, "total": total, "page": page, "pages": (total + limit - 1) // limit}
    return make_response(success=True, message="Rooms list retrieved.", data=res, extra_compat=res)

@rooms_router.get("/{id}")
def get_room(id: str, db: Session = Depends(get_db)):
    room = db.query(Room).filter_by(id=id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found.")
    res = {
        "id": room.id, "roomNumber": room.roomNumber, "roomType": room.roomType, "capacity": room.capacity,
        "buildingId": room.buildingId, "floor": room.floor, "projector": room.projector,
        "smartBoard": room.smartBoard, "airConditioning": room.airConditioning, "status": room.status, "departmentId": room.departmentId
    }
    return make_response(success=True, message="Room found.", data=res, extra_compat=res)

@rooms_router.put("/{id}")
def update_room(id: str, payload: RoomSchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    room = db.query(Room).filter_by(id=id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found.")
    
    existing = db.query(Room).filter(Room.id != id).filter_by(roomNumber=payload.roomNumber).first()
    if existing:
        raise HTTPException(status_code=400, detail="Room Number already exists.")
    
    room.roomNumber = payload.roomNumber
    room.roomType = payload.roomType
    room.capacity = payload.capacity
    room.buildingId = payload.buildingId
    room.floor = payload.floor
    room.projector = payload.projector
    room.smartBoard = payload.smartBoard
    room.airConditioning = payload.airConditioning
    room.status = payload.status
    room.departmentId = payload.departmentId
    db.commit()
    log_audit(db, current_user.id, "ROOM_UPDATE", f"Updated room {room.roomNumber}.")
    return make_response(success=True, message="Room updated.", data={})

@rooms_router.delete("/{id}")
def delete_room(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    room = db.query(Room).filter_by(id=id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found.")
    db.delete(room)
    db.commit()
    log_audit(db, current_user.id, "ROOM_DELETE", f"Deleted room {room.roomNumber}.")
    return make_response(success=True, message="Room deleted.", data={})

# -------------------------------------------------------------
# 10. LABORATORY ROUTER
# -------------------------------------------------------------
laboratories_router = APIRouter()

@laboratories_router.post("")
def create_laboratory(payload: LaboratorySchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    existing = db.query(Laboratory).filter_by(labName=payload.labName).first()
    if existing:
        raise HTTPException(status_code=400, detail="Laboratory Name already exists.")
    
    lab = Laboratory(
        id=str(uuid.uuid4()),
        labName=payload.labName,
        departmentId=payload.departmentId,
        capacity=payload.capacity,
        systems=payload.systems,
        software=payload.software,
        labAssistant=payload.labAssistant
    )
    db.add(lab)
    db.commit()
    db.refresh(lab)
    log_audit(db, current_user.id, "LAB_CREATE", f"Created lab {lab.labName}.")
    res = {"id": lab.id, "labName": lab.labName}
    return make_response(success=True, message="Laboratory created successfully.", data=res, extra_compat=res)

@laboratories_router.get("")
def list_laboratories(search: Optional[str] = None, departmentId: Optional[str] = None, page: int = 1, limit: int = 10, db: Session = Depends(get_db)):
    query = db.query(Laboratory)
    if departmentId:
        query = query.filter_by(departmentId=departmentId)
    if search:
        query = query.filter(Laboratory.labName.ilike(f"%{search}%"))
    
    total = query.count()
    items = query.offset((page - 1) * limit).limit(limit).all()
    
    data = [{
        "id": x.id, "labName": x.labName, "capacity": x.capacity, "systems": x.systems, "software": x.software,
        "labAssistant": x.labAssistant, "departmentId": x.departmentId, "departmentName": x.department.name if x.department else None
    } for x in items]
    
    res = {"laboratories": data, "total": total, "page": page, "pages": (total + limit - 1) // limit}
    return make_response(success=True, message="Laboratories list retrieved.", data=res, extra_compat=res)

@laboratories_router.get("/{id}")
def get_laboratory(id: str, db: Session = Depends(get_db)):
    lab = db.query(Laboratory).filter_by(id=id).first()
    if not lab:
        raise HTTPException(status_code=404, detail="Laboratory not found.")
    res = {
        "id": lab.id, "labName": lab.labName, "departmentId": lab.departmentId, "capacity": lab.capacity,
        "systems": lab.systems, "software": lab.software, "labAssistant": lab.labAssistant
    }
    return make_response(success=True, message="Laboratory found.", data=res, extra_compat=res)

@laboratories_router.put("/{id}")
def update_laboratory(id: str, payload: LaboratorySchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    lab = db.query(Laboratory).filter_by(id=id).first()
    if not lab:
        raise HTTPException(status_code=404, detail="Laboratory not found.")
    
    existing = db.query(Laboratory).filter(Laboratory.id != id).filter_by(labName=payload.labName).first()
    if existing:
        raise HTTPException(status_code=400, detail="Laboratory Name already exists.")
    
    lab.labName = payload.labName
    lab.departmentId = payload.departmentId
    lab.capacity = payload.capacity
    lab.systems = payload.systems
    lab.software = payload.software
    lab.labAssistant = payload.labAssistant
    db.commit()
    log_audit(db, current_user.id, "LAB_UPDATE", f"Updated laboratory {lab.labName}.")
    return make_response(success=True, message="Laboratory updated.", data={})

@laboratories_router.delete("/{id}")
def delete_laboratory(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    lab = db.query(Laboratory).filter_by(id=id).first()
    if not lab:
        raise HTTPException(status_code=404, detail="Laboratory not found.")
    db.delete(lab)
    db.commit()
    log_audit(db, current_user.id, "LAB_DELETE", f"Deleted laboratory {lab.labName}.")
    return make_response(success=True, message="Laboratory deleted.", data={})

# -------------------------------------------------------------
# 11. FACULTY ASSIGNMENT ROUTER
# -------------------------------------------------------------
faculty_assignments_router = APIRouter()

@faculty_assignments_router.post("")
def create_faculty_assignment(payload: FacultyAssignmentSchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    # Validate the assigned user has the role of Teacher
    faculty = db.query(User).filter_by(id=payload.facultyId).first()
    if not faculty or faculty.role.name != "TEACHER":
        raise HTTPException(status_code=400, detail="The assigned user must be a designated Teacher.")

    # Prevent duplicate assignments
    existing = db.query(FacultyAssignment).filter_by(
        facultyId=payload.facultyId,
        subjectId=payload.subjectId,
        sectionId=payload.sectionId,
        semesterId=payload.semesterId,
        academicYearId=payload.academicYearId
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="This faculty assignment already exists.")

    fa = FacultyAssignment(
        id=str(uuid.uuid4()),
        departmentId=payload.departmentId,
        subjectId=payload.subjectId,
        facultyId=payload.facultyId,
        sectionId=payload.sectionId,
        semesterId=payload.semesterId,
        academicYearId=payload.academicYearId
    )
    db.add(fa)
    db.commit()
    db.refresh(fa)
    log_audit(db, current_user.id, "FACULTY_ASSIGNMENT_CREATE", f"Assigned teacher {faculty.name} to subject {fa.subjectId}.")
    res = {"id": fa.id}
    return make_response(success=True, message="Faculty assigned successfully.", data=res, extra_compat=res)

@faculty_assignments_router.get("")
def list_faculty_assignments(facultyId: Optional[str] = None, page: int = 1, limit: int = 10, db: Session = Depends(get_db)):
    query = db.query(FacultyAssignment)
    if facultyId:
        query = query.filter_by(facultyId=facultyId)
        
    total = query.count()
    items = query.offset((page - 1) * limit).limit(limit).all()
    
    data = [{
        "id": x.id,
        "departmentId": x.departmentId, "departmentName": x.department.name if x.department else None,
        "subjectId": x.subjectId, "subjectName": x.subject.name if x.subject else None,
        "facultyId": x.facultyId, "facultyName": x.faculty.name if x.faculty else None,
        "sectionId": x.sectionId, "sectionName": x.section.name if x.section else None,
        "semesterId": x.semesterId, "semesterNumber": x.semester.semesterNumber if x.semester else None,
        "academicYearId": x.academicYearId, "academicYearName": x.academicYear.name if x.academicYear else None
    } for x in items]
    
    res = {"assignments": data, "total": total, "page": page, "pages": (total + limit - 1) // limit}
    return make_response(success=True, message="Faculty assignments retrieved.", data=res, extra_compat=res)

@faculty_assignments_router.delete("/{id}")
def delete_faculty_assignment(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_no_password_force)):
    fa = db.query(FacultyAssignment).filter_by(id=id).first()
    if not fa:
        raise HTTPException(status_code=404, detail="Faculty assignment not found.")
    db.delete(fa)
    db.commit()
    log_audit(db, current_user.id, "FACULTY_ASSIGNMENT_DELETE", f"Deleted assignment {fa.id}.")
    return make_response(success=True, message="Faculty assignment removed.", data={})
