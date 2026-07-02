# CampusGPT X - API Documentation & Integration Guide

Welcome to the CampusGPT X developer API portal. This document details the endpoints, request/response models, and security/session policies.

---

## 🔒 Authentication & Authorization

All API calls (except `/health` and `/auth/login`) require a valid JSON Web Token (JWT) provided in either the `Authorization` header or as an HTTP-only cookie.

---

## 📊 Standard API Response Envelope

Every endpoint returns a unified JSON envelope:

### Successful Operation
```json
{
  "success": true,
  "message": "Resource action details",
  "data": {
    "key": "value"
  },
  "errors": null
}
```

---

## 🚀 API Endpoint Reference

### 1. System Health
* **Route**: `GET /api/v1/health`

---

### 2. Authentication
* `POST /api/v1/auth/login` - User authentication and JWT distribution.
* `POST /api/v1/auth/change-password` - Set new password keys for authenticated accounts.

---

### 3. User Directory
* `GET /api/v1/users` - Paginated and sorted active campus account directory.
* `POST /api/v1/users/import` - Bulk upload Excel sheets parsing new student/staff profiles.

---

### 4. Student Portal Module
* `GET /api/v1/student/dashboard` - Get overall attendance percentage, CGPA, completed credits, upcoming classes, timetables, and AI study recommendations.

---

### 5. Faculty Portal Module
* `GET /api/v1/faculty/dashboard` - Retrieve welcome cards, timetable metrics, assigned subject rosters, and pending evaluations statistics.

---

### 6. Smart Timetable Module (New in Day 7)

#### Calendar Configurations
* `POST /api/v1/timetable/calendar` - Setup calendar config (working days).
* `GET /api/v1/timetable/calendar` - Fetch current active calendar parameters.
* `POST /api/v1/timetable/calendar/events` - Add holidays, exam days, and event dates.
* `GET /api/v1/timetable/calendar/events` - List calendar events order by date.

#### Time Slot Configurations
* `POST /api/v1/timetable/slots` - Create custom period time slots (overlaps validated).
* `GET /api/v1/timetable/slots` - List time slots ordered by start times.

#### Conflict Validation Check
* `POST /api/v1/timetable/validate` - Checks a target cell mapping proposal against published schedules. Returns clashes found.

#### Timetable Grid Layouts CRUD
* `POST /api/v1/timetable/grids` - Save timetable grid layout container header.
* `GET /api/v1/timetable/grids` - List all grids.
* `GET /api/v1/timetable/grids/{id}` - Load grid details and entry cell lists.
* `POST /api/v1/timetable/grids/{id}/entries` - Map a cell (Subject, Room, Teacher) to a day and slot (conflicts pre-validated).

#### Role-Specific Schedules Queries
* `GET /api/v1/timetable/student/schedule` - Fetch personal weekly schedule for a student.
* `GET /api/v1/timetable/faculty/schedule` - Fetch personal weekly teaching schedule for an instructor.

#### Substitute swapping
* `POST /api/v1/timetable/substitute` - Generate substitute faculty swap requests.
* `GET /api/v1/timetable/substitute` - Retrieve all substitutions logs.
* `POST /api/v1/timetable/substitute/{id}/approve` - Approve dynamic teacher swapping.

#### Approvals workflow
* `POST /api/v1/timetable/approval` - Progress layout headers along approval stage checks (Draft -> Dept -> Academic -> Master Admin published status).

---

### 7. Attendance Management Module (New in Day 8)

#### Sessions Management
* `POST /api/v1/attendance/session` - Create classroom attendance session.
* `GET /api/v1/attendance/session/{id}/students` - Retrieve section roster for marking attendance (returns students array).
* `POST /api/v1/attendance/session/{id}/records` - Mark attendance list (saves draft or finalizes records).
* `GET /api/v1/attendance/sessions` - List attendance sessions.

#### Student View
* `GET /api/v1/attendance/student/my-attendance` - Fetch personal weekly/monthly and subject-wise summaries for student.

#### Correction Requests
* `POST /api/v1/attendance/corrections` - Students submit a correction request.
* `GET /api/v1/attendance/corrections` - Load correction requests (students view own, teachers view their classes).
* `POST /api/v1/attendance/corrections/{id}/review` - Instructors review correction request (Approve/Reject with comments).

#### Defaulters
* `GET /api/v1/attendance/defaulters` - Pull defaulter listings (Below 75%, 65%, 50% benchmarks).

---

### 8. Dynamic QR Attendance Module (New in Day 9)

#### Session Operations
* `POST /api/v1/qr-attendance/session` - Create QR Session and active countdown code.
* `GET /api/v1/qr-attendance/session/{id}/code` - Fetch active dynamic access key token. Automatically rotates code on request if expired.
* `POST /api/v1/qr-attendance/scan` - Students scan key token submitting geolocations coordinates and browser device fingerprints.
* `POST /api/v1/qr-attendance/session/{id}/close` - Faculty closes active session.

#### Live Status Polling
* `GET /api/v1/qr-attendance/session/{id}/status` - Live stats detailing Present List, Pending List, and attendance counts.

---

### 9. Face Recognition Module (New in Day 10)

#### Face Registration
* `POST /api/v1/face/register` - Captures 5 angles and registers face profiles.
* `GET /api/v1/face/registrations` - Lists registration logs for review.
* `POST /api/v1/face/registrations/{id}/review` - Admins approve or reject biometric applications.
* `DELETE /api/v1/face/registrations/{id}` - Reset or delete face profile embeddings.

#### Face Recognition Verification
* `POST /api/v1/face/login` - Facially authenticates users with cosine similarity, liveness metrics, and anti-spoof checks.
* `POST /api/v1/face/verify` - Biometric comparison helper checking features matching percentages.
* `POST /api/v1/face/attendance` - Student facial recognitions check-in marking classroom attendance.

#### Administrative statistics
* `GET /api/v1/face/statistics` - Recognition logs, liveness passed counts, and failed verification indicators.

---

### 10. Assignment Management Module (New in Day 11)

#### Assignment Operations
* `POST /api/v1/assignments` - Faculty creates a new assignment with configurations.
* `GET /api/v1/assignments` - Get assignments with query filters, search, and page variables.
* `GET /api/v1/assignments/{id}` - Details of an assignment.
* `PUT /api/v1/assignments/{id}` - Edit details.
* `DELETE /api/v1/assignments/{id}` - Delete assignment.

#### Submission Operations
* `POST /api/v1/assignments/{id}/submit` - Student uploads assignment file attachments.
* `GET /api/v1/assignments/{id}/submissions` - Faculty fetches all student uploads.

#### Grading Operations
* `POST /api/v1/assignments/submissions/{submission_id}/grade` - Faculty evaluations grading submissions.

#### Statistics Operations
* `GET /api/v1/assignments/statistics/summary` - Faculty and Student summary dashboard metrics.

---

### 11. Examination Management Module (New in Day 12)

#### Exam Operations
* `POST /api/v1/exams` - Creates a new exam with department, course, and date properties.
* `GET /api/v1/exams` - Retrieves a filtered and searched exam list.
* `GET /api/v1/exams/{id}` - Detail view.
* `PUT /api/v1/exams/{id}` - Updates exam metadata.
* `DELETE /api/v1/exams/{id}` - Deletes exam.

#### Scheduling & Allocations
* `POST /api/v1/exams/{id}/schedule` - Sets room and staff invigilators with conflict overlap checking.
* `POST /api/v1/exams/{id}/hallticket` - Issues a student admit card.
* `POST /api/v1/exams/halltickets/{ticket_id}/seat-allocation` - Binds bench seat numbers with duplicate check protection.

#### Question Papers
* `POST /api/v1/exams/question-papers` - Faculty uploads a question paper.
* `POST /api/v1/exams/question-papers/{qp_id}/review` - Admins approve or reject the draft.

#### Statistics
* `GET /api/v1/exams/statistics/summary` - Live dashboards statistics counts.

---

### 12. Result Management Module (New in Day 13)

#### Grade Scheme Configurations
* `POST /api/v1/results/schemes` - Admin configures custom Grade scale boundaries.
* `GET /api/v1/results/schemes` - Lists program grade schemes.

#### Mark Entry & Calculators
* `POST /api/v1/results/marks` - Faculty enters marks for theory, assignments, labs, or grace. Automatically calculates overall GPA.

#### Publishing Workflow
* `POST /api/v1/results/{id}/publish` - Transitions card status (Draft, Dept Review, Publish).

#### Transcripts & Grade Cards
* `POST /api/v1/results/transcripts` - Generates transcript verification cards with digital signature signatures.
* `GET /api/v1/results/transcripts` - Lists generated transcripts.

#### Revaluations
* `POST /api/v1/results/revaluation` - Students apply for revaluation.
* `POST /api/v1/results/revaluation/{id}/review` - Instructors review revaluation requests.
* `GET /api/v1/results/revaluation` - Lists active revaluations.

#### Rankings & Merit
* `GET /api/v1/results/merit-list` - Compiles rank lists by semester.
* `GET /api/v1/results/analytics` - Compiles departmental analytics records.
