import json
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.core.auth_middleware import get_current_user_no_password_force
from app.core.responses import make_response
from app.models.models import (
    User, Subject, Room, Laboratory, AcademicCalendar, CalendarEvent, TimeSlot,
    Timetable, TimetableEntry, SubstituteFaculty, TimetableApproval
)

router = APIRouter()

# -------------------------------------------------------------
# PYDANTIC SCHEMAS
# -------------------------------------------------------------
class CalendarCreateSchema(BaseModel):
    academicYearId: str
    workingDays: List[str] # ["MONDAY", "TUESDAY"]

class CalendarEventCreateSchema(BaseModel):
    calendarId: str
    title: str
    eventDate: datetime
    type: str # HOLIDAY, EXAM_DAY, COLLEGE_EVENT, SPECIAL_WORKING_DAY
    description: Optional[str] = None

class TimeSlotCreateSchema(BaseModel):
    name: str
    startTime: str
    endTime: str
    type: str # CLASS, BREAK, LAB, EXTRA

class TimetableCreateSchema(BaseModel):
    name: str
    academicYearId: str
    semesterId: str
    sectionId: str

class TimetableEntryCreateSchema(BaseModel):
    dayOfWeek: str
    timeSlotId: str
    subjectId: Optional[str] = None
    facultyId: Optional[str] = None
    roomId: Optional[str] = None
    labId: Optional[str] = None

class ConflictCheckSchema(BaseModel):
    timetableId: str
    dayOfWeek: str
    timeSlotId: str
    facultyId: Optional[str] = None
    roomId: Optional[str] = None
    labId: Optional[str] = None

class SubstituteCreateSchema(BaseModel):
    date: datetime
    timetableEntryId: str
    substituteFacultyId: str

class ApprovalSchema(BaseModel):
    timetableId: str
    stage: str # DEPT_REVIEW, ACADEMIC_OFFICE, MASTER_ADMIN
    status: str # APPROVED, REJECTED
    remarks: Optional[str] = None

# -------------------------------------------------------------
# CONFLICT DETECTION ALGORITHMS
# -------------------------------------------------------------
def check_timetable_conflicts(db: Session, timetable_id: str, day: str, slot_id: str, faculty_id: Optional[str], room_id: Optional[str], lab_id: Optional[str]):
    conflicts = []
    
    # 1. Faculty Clash (Assigned to another subject at the same time)
    if faculty_id:
        f_clash = db.query(TimetableEntry).join(Timetable).filter(
            TimetableEntry.dayOfWeek == day,
            TimetableEntry.timeSlotId == slot_id,
            TimetableEntry.facultyId == faculty_id,
            Timetable.status == "PUBLISHED"
        ).first()
        if f_clash:
            conflicts.append(f"Faculty is already assigned to {f_clash.subject.name if f_clash.subject else 'another class'} in Section {f_clash.timetable.section.name if f_clash.timetable.section else ''}.")

    # 2. Room Clash (Occupied by another class at the same time)
    if room_id:
        r_clash = db.query(TimetableEntry).join(Timetable).filter(
            TimetableEntry.dayOfWeek == day,
            TimetableEntry.timeSlotId == slot_id,
            TimetableEntry.roomId == room_id,
            Timetable.status == "PUBLISHED"
        ).first()
        if r_clash:
            conflicts.append(f"Room is already occupied by Section {r_clash.timetable.section.name if r_clash.timetable.section else ''}.")

    # 3. Lab Clash (Occupied by another class at the same time)
    if lab_id:
        l_clash = db.query(TimetableEntry).join(Timetable).filter(
            TimetableEntry.dayOfWeek == day,
            TimetableEntry.timeSlotId == slot_id,
            TimetableEntry.labId == lab_id,
            Timetable.status == "PUBLISHED"
        ).first()
        if l_clash:
            conflicts.append(f"Laboratory is already occupied by Section {l_clash.timetable.section.name if l_clash.timetable.section else ''}.")

    # 4. Student/Section Clash (Section already has something scheduled at this time)
    s_clash = db.query(TimetableEntry).filter(
        TimetableEntry.timetableId == timetable_id,
        TimetableEntry.dayOfWeek == day,
        TimetableEntry.timeSlotId == slot_id
    ).first()
    if s_clash:
        conflicts.append(f"This section already has a class scheduled ({s_clash.subject.name if s_clash.subject else 'Break'}).")

    return conflicts

# -------------------------------------------------------------
# API ROUTERS
# -------------------------------------------------------------

# Calendar Config
@router.post("/calendar")
def create_academic_calendar(payload: CalendarCreateSchema, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    if current_user.role.name != "MASTER_ADMIN":
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    cal = AcademicCalendar(
        id=str(uuid.uuid4()),
        academicYearId=payload.academicYearId,
        workingDays=json.dumps(payload.workingDays)
    )
    db.add(cal)
    db.commit()
    return make_response(success=True, message="Academic calendar created.", data={"id": cal.id})

@router.get("/calendar")
def get_academic_calendar(db: Session = Depends(get_db)):
    cal = db.query(AcademicCalendar).filter().first()
    if not cal:
        return make_response(success=True, message="No calendar configured.", data=None)
    data = {
        "id": cal.id,
        "academicYearId": cal.academicYearId,
        "workingDays": json.loads(cal.workingDays)
    }
    return make_response(success=True, message="Calendar fetched.", data=data, extra_compat=data)

# Calendar Events
@router.post("/calendar/events")
def create_calendar_event(payload: CalendarEventCreateSchema, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    if current_user.role.name != "MASTER_ADMIN":
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    evt = CalendarEvent(
        id=str(uuid.uuid4()),
        calendarId=payload.calendarId,
        title=payload.title,
        eventDate=payload.eventDate,
        type=payload.type,
        description=payload.description
    )
    db.add(evt)
    db.commit()
    return make_response(success=True, message="Calendar event added.", data={"id": evt.id})

@router.get("/calendar/events")
def list_calendar_events(db: Session = Depends(get_db)):
    evts = db.query(CalendarEvent).order_by(CalendarEvent.eventDate.asc()).all()
    data = [{
        "id": e.id,
        "title": e.title,
        "eventDate": e.eventDate,
        "type": e.type,
        "description": e.description
    } for e in evts]
    return make_response(success=True, message="Calendar events fetched.", data={"events": data}, extra_compat={"events": data})

# Custom Time slots
@router.post("/slots")
def create_time_slot(payload: TimeSlotCreateSchema, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    if current_user.role.name != "MASTER_ADMIN":
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    # Overlap Validation
    overlap = db.query(TimeSlot).filter(
        TimeSlot.startTime < payload.endTime,
        TimeSlot.endTime > payload.startTime
    ).first()
    if overlap:
        raise HTTPException(status_code=400, detail=f"Overlapping period with {overlap.name}.")
        
    slot = TimeSlot(
        id=str(uuid.uuid4()),
        name=payload.name,
        startTime=payload.startTime,
        endTime=payload.endTime,
        type=payload.type
    )
    db.add(slot)
    db.commit()
    return make_response(success=True, message="Time slot config saved.", data={"id": slot.id})

@router.get("/slots")
def list_time_slots(db: Session = Depends(get_db)):
    slots = db.query(TimeSlot).order_by(TimeSlot.startTime.asc()).all()
    data = [{
        "id": s.id,
        "name": s.name,
        "startTime": s.startTime,
        "endTime": s.endTime,
        "type": s.type
    } for s in slots]
    return make_response(success=True, message="Time slots listed.", data={"slots": data}, extra_compat={"slots": data})

# Conflict Checker Validation Route
@router.post("/validate")
def validate_timetable_slot(payload: ConflictCheckSchema, db: Session = Depends(get_db)):
    conflicts = check_timetable_conflicts(
        db, payload.timetableId, payload.dayOfWeek, payload.timeSlotId,
        payload.facultyId, payload.roomId, payload.labId
    )
    return make_response(
        success=len(conflicts) == 0,
        message="Conflict checks completed." if len(conflicts) == 0 else "Conflicts detected.",
        data={"conflicts": conflicts},
        extra_compat={"conflicts": conflicts}
    )

# Timetables Management
@router.post("/grids")
def create_timetable_header(payload: TimetableCreateSchema, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    if current_user.role.name != "MASTER_ADMIN":
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    tt = Timetable(
        id=str(uuid.uuid4()),
        name=payload.name,
        academicYearId=payload.academicYearId,
        semesterId=payload.semesterId,
        sectionId=payload.sectionId
    )
    db.add(tt)
    db.commit()
    return make_response(success=True, message="Timetable grid header saved.", data={"id": tt.id})

@router.get("/grids")
def list_timetable_grids(db: Session = Depends(get_db)):
    grids = db.query(Timetable).all()
    data = [{
        "id": g.id,
        "name": g.name,
        "section": g.section.name if g.section else "N/A",
        "semester": g.semester.semesterNumber if g.semester else 1,
        "status": g.status,
        "version": g.version
    } for g in grids]
    return make_response(success=True, message="Timetable grids retrieved.", data={"grids": data}, extra_compat={"grids": data})

@router.get("/grids/{id}")
def get_timetable_grid_entries(id: str, db: Session = Depends(get_db)):
    tt = db.query(Timetable).filter_by(id=id).first()
    if not tt:
        raise HTTPException(status_code=404, detail="Grid not found.")
        
    entries = db.query(TimetableEntry).filter_by(timetableId=id).all()
    data = [{
        "id": e.id,
        "dayOfWeek": e.dayOfWeek,
        "timeSlotId": e.timeSlotId,
        "timeSlotName": e.timeSlot.name if e.timeSlot else "N/A",
        "subjectId": e.subjectId,
        "subjectName": e.subject.name if e.subject else "",
        "facultyId": e.facultyId,
        "facultyName": e.faculty.name if e.faculty else "",
        "roomId": e.roomId,
        "roomNumber": e.room.roomNumber if e.room else "",
        "labId": e.labId,
        "labName": e.lab.labName if e.lab else ""
    } for e in entries]
    return make_response(success=True, message="Grid entries loaded.", data={"timetable": {
        "id": tt.id,
        "name": tt.name,
        "status": tt.status,
        "entries": data
    }}, extra_compat={"timetable": {
        "id": tt.id,
        "name": tt.name,
        "status": tt.status,
        "entries": data
    }})

@router.post("/grids/{id}/entries")
def save_timetable_entry(id: str, payload: TimetableEntryCreateSchema, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    if current_user.role.name != "MASTER_ADMIN":
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    # Check for conflicts
    conflicts = check_timetable_conflicts(
        db, id, payload.dayOfWeek, payload.timeSlotId,
        payload.facultyId, payload.roomId, payload.labId
    )
    if conflicts:
        raise HTTPException(status_code=400, detail=f"Conflicts detected: {', '.join(conflicts)}")
        
    # Delete duplicate slot mapping if exists
    existing = db.query(TimetableEntry).filter_by(timetableId=id, dayOfWeek=payload.dayOfWeek, timeSlotId=payload.timeSlotId).first()
    if existing:
        db.delete(existing)
        
    entry = TimetableEntry(
        id=str(uuid.uuid4()),
        timetableId=id,
        dayOfWeek=payload.dayOfWeek,
        timeSlotId=payload.timeSlotId,
        subjectId=payload.subjectId,
        facultyId=payload.facultyId,
        roomId=payload.roomId,
        labId=payload.labId
    )
    db.add(entry)
    db.commit()
    return make_response(success=True, message="Timetable entry saved.", data={"id": entry.id})

# Role Schedules
@router.get("/student/schedule")
def get_student_schedule(current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    if current_user.role.name != "STUDENT":
        raise HTTPException(status_code=403, detail="Access denied.")
    if not current_user.sectionId:
        return make_response(success=True, message="Student has no section assigned.", data={"schedule": []}, extra_compat={"schedule": []})
        
    tt = db.query(Timetable).filter_by(sectionId=current_user.sectionId, status="PUBLISHED").first()
    if not tt:
        return make_response(success=True, message="No published timetable for student section.", data={"schedule": []}, extra_compat={"schedule": []})
        
    entries = db.query(TimetableEntry).filter_by(timetableId=tt.id).all()
    data = [{
        "dayOfWeek": e.dayOfWeek,
        "timeSlotName": e.timeSlot.name if e.timeSlot else "N/A",
        "startTime": e.timeSlot.startTime if e.timeSlot else "",
        "endTime": e.timeSlot.endTime if e.timeSlot else "",
        "subjectName": e.subject.name if e.subject else "",
        "roomNumber": e.room.roomNumber if e.room else "",
        "facultyName": e.faculty.name if e.faculty else ""
    } for e in entries]
    return make_response(success=True, message="Student schedule loaded.", data={"schedule": data}, extra_compat={"schedule": data})

@router.get("/faculty/schedule")
def get_faculty_schedule(current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    if current_user.role.name != "TEACHER":
        raise HTTPException(status_code=403, detail="Access denied.")
        
    entries = db.query(TimetableEntry).join(Timetable).filter(
        TimetableEntry.facultyId == current_user.id,
        Timetable.status == "PUBLISHED"
    ).all()
    data = [{
        "dayOfWeek": e.dayOfWeek,
        "timeSlotName": e.timeSlot.name if e.timeSlot else "N/A",
        "startTime": e.timeSlot.startTime if e.timeSlot else "",
        "endTime": e.timeSlot.endTime if e.timeSlot else "",
        "subjectName": e.subject.name if e.subject else "",
        "roomNumber": e.room.roomNumber if e.room else "",
        "sectionName": e.timetable.section.name if e.timetable.section else ""
    } for e in entries]
    return make_response(success=True, message="Faculty schedule loaded.", data={"schedule": data}, extra_compat={"schedule": data})

# Substitute Faculty
@router.post("/substitute")
def create_substitute_request(payload: SubstituteCreateSchema, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    entry = db.query(TimetableEntry).filter_by(id=payload.timetableEntryId).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Timetable entry not found.")
        
    sub = SubstituteFaculty(
        id=str(uuid.uuid4()),
        date=payload.date,
        timetableEntryId=payload.timetableEntryId,
        originalFacultyId=entry.facultyId,
        substituteFacultyId=payload.substituteFacultyId
    )
    db.add(sub)
    db.commit()
    return make_response(success=True, message="Substitute request logged.", data={"id": sub.id})

@router.get("/substitute")
def get_substitute_requests(db: Session = Depends(get_db)):
    requests = db.query(SubstituteFaculty).all()
    data = [{
        "id": r.id,
        "date": r.date,
        "originalFaculty": r.originalFaculty.name if r.originalFaculty else "N/A",
        "substituteFaculty": r.substituteFaculty.name if r.substituteFaculty else "N/A",
        "status": r.status,
        "subjectName": r.timetableEntry.subject.name if r.timetableEntry and r.timetableEntry.subject else "N/A"
    } for r in requests]
    return make_response(success=True, message="Substitute list fetched.", data={"substitutes": data}, extra_compat={"substitutes": data})

@router.post("/substitute/{id}/approve")
def approve_substitute_request(id: str, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    if current_user.role.name != "MASTER_ADMIN":
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    req = db.query(SubstituteFaculty).filter_by(id=id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found.")
    req.status = "APPROVED"
    db.commit()
    return make_response(success=True, message="Substitute swapping approved.", data={})

# Workflow Approvals
@router.post("/approval")
def submit_timetable_approval(payload: ApprovalSchema, current_user: User = Depends(get_current_user_no_password_force), db: Session = Depends(get_db)):
    if current_user.role.name != "MASTER_ADMIN":
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    tt = db.query(Timetable).filter_by(id=payload.timetableId).first()
    if not tt:
        raise HTTPException(status_code=404, detail="Timetable not found.")
        
    log = TimetableApproval(
        id=str(uuid.uuid4()),
        timetableId=payload.timetableId,
        userId=current_user.id,
        stage=payload.stage,
        status=payload.status,
        remarks=payload.remarks
    )
    db.add(log)
    
    if payload.status == "APPROVED" and payload.stage == "MASTER_ADMIN":
        tt.status = "PUBLISHED"
        
    db.commit()
    return make_response(success=True, message="Timetable stage update logged.", data={})
