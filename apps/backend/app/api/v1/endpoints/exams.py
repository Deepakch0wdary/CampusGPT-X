from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, asc
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.core.dependencies import get_db
from app.core.auth_middleware import get_current_user_no_password_force
from app.core.rbac_middleware import RoleChecker
from app.core.responses import make_response
from app.models.models import (
    Exam, ExamSchedule, ExamRoom, ExamInvigilator, HallTicket,
    SeatAllocation, QuestionPaper, ExamAudit, User, Subject,
    AcademicYear, Department, Program, Semester, Section
)

router = APIRouter()

# --- Pydantic Schemas ---
class ExamCreate(BaseModel):
    examName: str
    examType: str
    academicYearId: str
    departmentId: str
    programId: str
    semesterId: str
    sectionId: str
    subjectId: str
    examDate: str # ISO Date String e.g. "2026-07-15T00:00:00Z"
    startTime: str # "09:30"
    endTime: str # "12:30"
    durationMinutes: int
    maxMarks: float
    passingMarks: float
    instructions: Optional[str] = None

class ExamUpdate(BaseModel):
    examName: Optional[str] = None
    examType: Optional[str] = None
    examDate: Optional[str] = None
    startTime: Optional[str] = None
    endTime: Optional[str] = None
    durationMinutes: Optional[int] = None
    maxMarks: Optional[float] = None
    passingMarks: Optional[float] = None
    instructions: Optional[str] = None
    status: Optional[str] = None

class ScheduleCreate(BaseModel):
    roomId: Optional[str] = None
    labId: Optional[str] = None
    invigilatorId: Optional[str] = None
    chiefSuperintendentId: Optional[str] = None
    observerId: Optional[str] = None

class HallTicketCreate(BaseModel):
    studentId: str
    examCenter: str
    seatNumber: Optional[str] = None

class SeatAllocateRequest(BaseModel):
    blockName: str
    roomNumber: str
    benchNumber: int
    seatNumber: str

class QuestionPaperCreate(BaseModel):
    examId: str
    fileUrl: str
    fileName: str

class QuestionPaperReview(BaseModel):
    status: str # APPROVED or REJECTED

class InvigilatorReport(BaseModel):
    attendanceStatus: str # PRESENT or ABSENT
    dutyReport: Optional[str] = None

# --- Helper Conflict Check ---
def check_scheduling_conflicts(
    db: Session,
    exam_id: str,
    date_val: datetime,
    start_str: str,
    end_str: str,
    room_id: Optional[str] = None,
    lab_id: Optional[str] = None,
    invigilator_id: Optional[str] = None
):
    # Parse times
    try:
        sh, sm = map(int, start_str.split(":"))
        eh, em = map(int, end_str.split(":"))
        new_start_min = sh * 60 + sm
        new_end_min = eh * 60 + em
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid startTime or endTime format (expected HH:MM)")

    # Fetch all schedules on the same day
    existing_schedules = db.query(ExamSchedule).join(Exam).filter(
        Exam.examDate == date_val,
        Exam.status == "ACTIVE"
    ).all()

    for sched in existing_schedules:
        # Parse existing schedule times
        esh, esm = map(int, sched.exam.startTime.split(":"))
        eeh, eem = map(int, sched.exam.endTime.split(":"))
        ex_start_min = esh * 60 + esm
        ex_end_min = eeh * 60 + eem

        # Check overlapping condition
        is_overlapping = (new_start_min < ex_end_min) and (new_end_min > ex_start_min)
        if not is_overlapping:
            continue

        # 1. Room conflict
        if room_id and sched.roomId == room_id:
            raise HTTPException(
                status_code=400,
                detail=f"Room overlap conflict: Room is already booked for exam '{sched.exam.examName}' at this time."
            )
        # 2. Lab conflict
        if lab_id and sched.labId == lab_id:
            raise HTTPException(
                status_code=400,
                detail=f"Laboratory overlap conflict: Lab is already booked for exam '{sched.exam.examName}' at this time."
            )
        # 3. Invigilator conflict
        if invigilator_id and sched.invigilatorId == invigilator_id:
            raise HTTPException(
                status_code=400,
                detail=f"Faculty Invigilator overlap conflict: Staff member is already booked for exam '{sched.exam.examName}'."
            )

# --- Endpoints ---

@router.post("", status_code=status.HTTP_201_CREATED)
def create_exam(
    payload: ExamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "TEACHER"]:
        raise HTTPException(status_code=403, detail="Not authorized to create exams")

    dt_val = datetime.fromisoformat(payload.examDate.replace("Z", "+00:00"))

    new_exam = Exam(
        examName=payload.examName,
        examType=payload.examType,
        academicYearId=payload.academicYearId,
        departmentId=payload.departmentId,
        programId=payload.programId,
        semesterId=payload.semesterId,
        sectionId=payload.sectionId,
        subjectId=payload.subjectId,
        facultyId=current_user.id,
        examDate=dt_val,
        startTime=payload.startTime,
        endTime=payload.endTime,
        durationMinutes=payload.durationMinutes,
        maxMarks=payload.maxMarks,
        passingMarks=payload.passingMarks,
        instructions=payload.instructions
    )
    db.add(new_exam)
    db.commit()
    db.refresh(new_exam)

    audit = ExamAudit(
        examId=new_exam.id,
        userId=current_user.id,
        action="CREATE_EXAM"
    )
    db.add(audit)
    db.commit()

    return make_response(
        success=True,
        message="Exam created successfully",
        data={
            "id": new_exam.id,
            "examName": new_exam.examName,
            "examType": new_exam.examType,
            "examDate": new_exam.examDate.isoformat(),
            "startTime": new_exam.startTime,
            "endTime": new_exam.endTime,
            "durationMinutes": new_exam.durationMinutes,
            "maxMarks": new_exam.maxMarks,
            "passingMarks": new_exam.passingMarks,
            "instructions": new_exam.instructions,
            "status": new_exam.status
        }
    )

@router.get("")
def list_exams(
    search: Optional[str] = None,
    examType: Optional[str] = None,
    status_filter: Optional[str] = None,
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    query = db.query(Exam)

    if current_user.role.name == "STUDENT":
        query = query.filter(Exam.sectionId == current_user.sectionId)
    elif current_user.role.name == "TEACHER":
        pass # Teachers can view all exams

    if search:
        query = query.filter(Exam.examName.like(f"%{search}%"))
    if examType:
        query = query.filter(Exam.examType == examType)
    if status_filter:
        query = query.filter(Exam.status == status_filter)

    total = query.count()
    exams = query.order_by(desc(Exam.createdAt)).offset((page - 1) * limit).limit(limit).all()

    return make_response(
        success=True,
        message="Exams list retrieved",
        data={
            "exams": [{
                "id": e.id,
                "examName": e.examName,
                "examType": e.examType,
                "examDate": e.examDate.isoformat() if e.examDate else None,
                "startTime": e.startTime,
                "endTime": e.endTime,
                "durationMinutes": e.durationMinutes,
                "maxMarks": e.maxMarks,
                "passingMarks": e.passingMarks,
                "instructions": e.instructions,
                "status": e.status
            } for e in exams],
            "total": total,
            "page": page,
            "limit": limit
        }
    )

@router.get("/{id}")
def get_exam_detail(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    exam = db.query(Exam).filter(Exam.id == id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    return make_response(
        success=True,
        message="Exam detail retrieved",
        data={
            "id": exam.id,
            "examName": exam.examName,
            "examType": exam.examType,
            "examDate": exam.examDate.isoformat() if exam.examDate else None,
            "startTime": exam.startTime,
            "endTime": exam.endTime,
            "durationMinutes": exam.durationMinutes,
            "maxMarks": exam.maxMarks,
            "passingMarks": exam.passingMarks,
            "instructions": exam.instructions,
            "status": exam.status
        }
    )

@router.put("/{id}")
def update_exam(
    id: str,
    payload: ExamUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "TEACHER"]:
        raise HTTPException(status_code=403, detail="Not authorized to edit exams")

    exam = db.query(Exam).filter(Exam.id == id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    update_data = payload.dict(exclude_unset=True)
    if "examDate" in update_data and update_data["examDate"]:
        update_data["examDate"] = datetime.fromisoformat(update_data["examDate"].replace("Z", "+00:00"))

    for k, v in update_data.items():
        setattr(exam, k, v)

    audit = ExamAudit(
        examId=exam.id,
        userId=current_user.id,
        action="UPDATE_EXAM"
    )
    db.add(audit)
    db.commit()
    db.refresh(exam)

    return make_response(
        success=True,
        message="Exam updated successfully",
        data={
            "id": exam.id,
            "examName": exam.examName,
            "examType": exam.examType,
            "examDate": exam.examDate.isoformat() if exam.examDate else None,
            "startTime": exam.startTime,
            "endTime": exam.endTime,
            "durationMinutes": exam.durationMinutes,
            "maxMarks": exam.maxMarks,
            "passingMarks": exam.passingMarks,
            "instructions": exam.instructions,
            "status": exam.status
        }
    )

@router.delete("/{id}")
def delete_exam(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "TEACHER"]:
        raise HTTPException(status_code=403, detail="Not authorized to delete exams")

    exam = db.query(Exam).filter(Exam.id == id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    db.delete(exam)
    db.commit()
    return make_response(success=True, message="Exam deleted successfully")

# --- Scheduling & Allocation ---
@router.post("/{id}/schedule")
def schedule_exam(
    id: str,
    payload: ScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "TEACHER"]:
        raise HTTPException(status_code=403, detail="Not authorized to schedule exams")

    exam = db.query(Exam).filter(Exam.id == id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    # Conflict check
    check_scheduling_conflicts(
        db=db,
        exam_id=exam.id,
        date_val=exam.examDate,
        start_str=exam.startTime,
        end_str=exam.endTime,
        room_id=payload.roomId,
        lab_id=payload.labId,
        invigilator_id=payload.invigilatorId
    )

    # Remove existing schedules for this exam
    db.query(ExamSchedule).filter(ExamSchedule.examId == exam.id).delete()

    schedule = ExamSchedule(
        examId=exam.id,
        roomId=payload.roomId,
        labId=payload.labId,
        invigilatorId=payload.invigilatorId,
        chiefSuperintendentId=payload.chiefSuperintendentId,
        observerId=payload.observerId
    )
    db.add(schedule)

    audit = ExamAudit(
        examId=exam.id,
        userId=current_user.id,
        action="SCHEDULE_EXAM"
    )
    db.add(audit)
    db.commit()
    db.refresh(schedule)

    return make_response(
        success=True,
        message="Exam scheduled successfully",
        data={
            "id": schedule.id,
            "examId": schedule.examId,
            "roomId": schedule.roomId,
            "labId": schedule.labId,
            "invigilatorId": schedule.invigilatorId
        }
    )

# --- Hall Ticket & Seating ---
@router.post("/{id}/hallticket")
def generate_hall_ticket(
    id: str,
    payload: HallTicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "TEACHER"]:
        raise HTTPException(status_code=403, detail="Not authorized to issue hall tickets")

    exam = db.query(Exam).filter(Exam.id == id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    # Prevent duplicate hall tickets
    existing_ticket = db.query(HallTicket).filter(
        HallTicket.studentId == payload.studentId,
        HallTicket.examId == exam.id
    ).first()
    if existing_ticket:
        raise HTTPException(status_code=400, detail="Hall ticket already generated for this student and exam")

    # Generate a unique hall ticket number
    ht_number = f"HT-{exam.examType[:3]}-{payload.studentId[:6]}-{datetime.utcnow().timestamp()}"

    new_ticket = HallTicket(
        hallTicketNumber=ht_number,
        studentId=payload.studentId,
        examId=exam.id,
        examCenter=payload.examCenter,
        seatNumber=payload.seatNumber
    )
    db.add(new_ticket)

    audit = ExamAudit(
        examId=exam.id,
        userId=current_user.id,
        action="DOWNLOAD_HALL_TICKET"
    )
    db.add(audit)
    db.commit()
    db.refresh(new_ticket)

    return make_response(
        success=True,
        message="Hall ticket generated successfully",
        data={
            "id": new_ticket.id,
            "hallTicketNumber": new_ticket.hallTicketNumber,
            "studentId": new_ticket.studentId,
            "examId": new_ticket.examId,
            "examCenter": new_ticket.examCenter,
            "seatNumber": new_ticket.seatNumber
        }
    )

@router.post("/halltickets/{ticket_id}/seat-allocation")
def allocate_seat(
    ticket_id: str,
    payload: SeatAllocateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "TEACHER"]:
        raise HTTPException(status_code=403, detail="Not authorized to allocate seats")

    ticket = db.query(HallTicket).filter(HallTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Hall ticket not found")

    # Prevent duplicate seats
    dup = db.query(SeatAllocation).filter(
        SeatAllocation.blockName == payload.blockName,
        SeatAllocation.roomNumber == payload.roomNumber,
        SeatAllocation.benchNumber == payload.benchNumber,
        SeatAllocation.seatNumber == payload.seatNumber
    ).first()
    if dup:
        raise HTTPException(status_code=400, detail="Seat number already allocated to another candidate in this block")

    # Remove previous allocation for this ticket
    db.query(SeatAllocation).filter(SeatAllocation.hallTicketId == ticket.id).delete()

    allocation = SeatAllocation(
        hallTicketId=ticket.id,
        blockName=payload.blockName,
        roomNumber=payload.roomNumber,
        benchNumber=payload.benchNumber,
        seatNumber=payload.seatNumber
    )
    db.add(allocation)

    # Bind seat number to ticket
    ticket.seatNumber = payload.seatNumber
    db.commit()
    db.refresh(allocation)

    return make_response(
        success=True,
        message="Seat allocated successfully",
        data={
            "id": allocation.id,
            "hallTicketId": allocation.hallTicketId,
            "blockName": allocation.blockName,
            "roomNumber": allocation.roomNumber,
            "benchNumber": allocation.benchNumber,
            "seatNumber": allocation.seatNumber
        }
    )

# --- Question Paper Workflow ---
@router.post("/question-papers", status_code=status.HTTP_201_CREATED)
def upload_question_paper(
    payload: QuestionPaperCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name not in ["MASTER_ADMIN", "TEACHER"]:
        raise HTTPException(status_code=403, detail="Not authorized to upload question papers")

    new_qp = QuestionPaper(
        examId=payload.examId,
        fileUrl=payload.fileUrl,
        fileName=payload.fileName,
        status="PENDING"
    )
    db.add(new_qp)

    audit = ExamAudit(
        examId=payload.examId,
        userId=current_user.id,
        action="UPLOAD_QUESTION_PAPER"
    )
    db.add(audit)
    db.commit()
    db.refresh(new_qp)

    return make_response(
        success=True,
        message="Question paper uploaded successfully",
        data={
            "id": new_qp.id,
            "examId": new_qp.examId,
            "fileUrl": new_qp.fileUrl,
            "fileName": new_qp.fileName,
            "status": new_qp.status
        }
    )

@router.post("/question-papers/{qp_id}/review")
def review_question_paper(
    qp_id: str,
    payload: QuestionPaperReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name != "MASTER_ADMIN":
        raise HTTPException(status_code=403, detail="Admin exclusive approval workflow")

    qp = db.query(QuestionPaper).filter(QuestionPaper.id == qp_id).first()
    if not qp:
        raise HTTPException(status_code=404, detail="Question paper not found")

    qp.status = payload.status
    qp.approvedById = current_user.id

    audit = ExamAudit(
        examId=qp.examId,
        userId=current_user.id,
        action="APPROVE_QUESTION_PAPER"
    )
    db.add(audit)
    db.commit()

    return make_response(
        success=True,
        message="Question paper reviewed successfully",
        data={
            "id": qp.id,
            "status": qp.status,
            "approvedById": qp.approvedById
        }
    )

# --- Student and Faculty Actions ---
@router.get("/student/halltickets")
def get_student_hall_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name != "STUDENT":
        raise HTTPException(status_code=403, detail="Student exclusive access")

    tickets = db.query(HallTicket).filter(HallTicket.studentId == current_user.id).all()
    return make_response(
        success=True,
        message="Hall tickets retrieved",
        data=[{
            "id": t.id,
            "hallTicketNumber": t.hallTicketNumber,
            "examId": t.examId,
            "examCenter": t.examCenter,
            "seatNumber": t.seatNumber
        } for t in tickets]
    )

@router.get("/invigilation/duties")
def get_invigilation_duties(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name != "TEACHER":
        raise HTTPException(status_code=403, detail="Teacher exclusive access")

    duties = db.query(ExamSchedule).filter(ExamSchedule.invigilatorId == current_user.id).all()
    return make_response(
        success=True,
        message="Invigilation duties retrieved",
        data=[{
            "id": d.id,
            "examId": d.examId,
            "roomId": d.roomId,
            "labId": d.labId
        } for d in duties]
    )

@router.post("/invigilation/{duty_id}/report")
def submit_duty_report(
    duty_id: str,
    payload: InvigilatorReport,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    if current_user.role.name != "TEACHER":
        raise HTTPException(status_code=403, detail="Teacher exclusive access")

    schedule = db.query(ExamSchedule).filter(ExamSchedule.id == duty_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Duty schedule not found")

    # Add or update invigilator report log
    report = db.query(ExamInvigilator).filter(
        ExamInvigilator.facultyId == current_user.id,
        ExamInvigilator.roomNumber == (schedule.room.roomNumber if schedule.room else "N/A")
    ).first()

    if not report:
        report = ExamInvigilator(
            facultyId=current_user.id,
            roomNumber=schedule.room.roomNumber if schedule.room else "N/A",
            blockName=schedule.room.building.name if schedule.room and schedule.room.building else "Main Block",
            shift="MORNING",
            attendanceStatus=payload.attendanceStatus,
            dutyReport=payload.dutyReport
        )
        db.add(report)
    else:
        report.attendanceStatus = payload.attendanceStatus
        report.dutyReport = payload.dutyReport

    db.commit()
    return make_response(success=True, message="Invigilation report submitted successfully")

@router.get("/statistics/summary")
def get_exam_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_no_password_force)
):
    total_active = db.query(Exam).filter(Exam.status == "ACTIVE").count()
    completed = db.query(Exam).filter(Exam.status == "COMPLETED").count()
    cancelled = db.query(Exam).filter(Exam.status == "CANCELLED").count()

    return make_response(
        success=True,
        message="Statistics summary retrieved",
        data={
            "totalActiveExams": total_active,
            "completedExams": completed,
            "cancelledExams": cancelled,
            "totalHallTickets": db.query(HallTicket).count()
        }
    )
