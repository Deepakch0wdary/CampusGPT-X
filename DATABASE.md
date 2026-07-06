# CampusGPT X - Database Schema Documentation

This document describes the database design, tables, relations, and optimization indexes implemented in **CampusGPT X**.

---

## 🗄️ Database Tables Overview

| Model | Table Name | Purpose | Primary / Unique Keys |
|---|---|---|---|
| **User** | `User` | Stores all core user login identity profiles. | `id` (PK), `email` (UQ), `username` (UQ) |
| **Role** | `Role` | System roles (e.g. MASTER_ADMIN, TEACHER, STUDENT). | `id` (PK), `name` (UQ) |
| **Permission** | `Permission` | Action capabilities (e.g. users:read, audits:read). | `id` (PK), `name` (UQ) |
| **UserPermission** | `UserPermission` | Custom direct RBAC permission bindings. | `id` (PK), `[userId, permissionId]` (UQ) |
| **UserSession** | `UserSession` | Track active device session logs. | `id` (PK) |
| **RefreshToken** | `RefreshToken` | Retain active JWT refresh tokens. | `id` (PK), `token` (UQ) |
| **LoginHistory** | `LoginHistory` | Audit trail of log attempts and lockdowns. | `id` (PK) |
| **AuditLog** | `AuditLog` | Track state changes and transactions. | `id` (PK) |
| **UserProfile** | `UserProfile` | User metadata (phone, bio, address, usn, emergency details). | `id` (PK), `userId` (UQ), `usn` (UQ) |
| **FacultyProfile** | `FacultyProfile` | Faculty metadata (employee ID, office location, specialization). | `id` (PK), `userId` (UQ), `employeeId` (UQ) |
| **Department** | `Department` | Academic/Administration Departments. | `id` (PK), `name` (UQ), `code` (UQ) |
| **Section** | `Section` | Student classroom divisions. | `id` (PK), `code` (UQ) |
| **Designation** | `Designation` | Staff designation tags (e.g. Professor). | `id` (PK), `name` (UQ), `code` (UQ) |
| **AcademicYear** | `AcademicYear` | Institutional calendar periods. | `id` (PK), `name` (UQ) |
| **Program** | `Program` | Academic curricula options (e.g. B.Tech). | `id` (PK), `name` (UQ), `code` (UQ) |
| **Course** | `Course` | Particular curricula course offerings. | `id` (PK), `code` (UQ) |
| **Semester** | `Semester` | Particular term blocks under programs. | `id` (PK) |
| **Subject** | `Subject` | Academic syllabus subjects. | `id` (PK), `code` (UQ) |
| **Building** | `Building` | Campus building structures. | `id` (PK), `name` (UQ), `code` (UQ) |
| **Room** | `Room` | Classrooms or laboratories inside buildings. | `id` (PK), `roomNumber` (UQ) |
| **Laboratory** | `Laboratory` | Multi-computer department labs. | `id` (PK), `labName` (UQ) |
| **FacultyAssignment**| `FacultyAssignment` | Map instructors to sections/subjects. | `id` (PK), `[facultyId, subjectId, sectionId, semesterId, academicYearId]` (UQ) |
| **AssignmentDef** | `AssignmentDef` | Master homework templates published by teachers. | `id` (PK) |
| **StudentAttendanceSummary** | `StudentAttendanceSummary` | Cumulative subject attendance counts. | `id` (PK), `[userId, subjectId]` (UQ) |
| **StudentResult** | `StudentResult` | Term grades, Internal/External scores. | `id` (PK), `[userId, subjectId]` (UQ) |
| **StudentAssignment** | `StudentAssignment` | Homework deadlines and submissions. | `id` (PK), `assignmentDefId` (FK) |
| **StudentCertificate** | `StudentCertificate` | Official study/bonafide document requests. | `id` (PK) |
| **StudentDocument** | `StudentDocument` | Student digital archive locker. | `id` (PK) |
| **StudentNotification** | `StudentNotification` | Tailored alert bulletins. | `id` (PK) |
| **FacultyNotes** | `FacultyNotes` | Uploaded resource links (PPTs, PDFs). | `id` (PK) |
| **FacultyQuiz** | `FacultyQuiz` | Scheduled question bank tests. | `id` (PK) |
| **FacultyLeave** | `FacultyLeave` | Leave request approvals tracker. | `id` (PK) |
| **FacultyNotification** | `FacultyNotification` | Staff-specific bulletin updates. | `id` (PK) |
| **AcademicCalendar** | `AcademicCalendar` | Calendar versions mapping working days. | `id` (PK) |
| **CalendarEvent** | `CalendarEvent` | Custom calendar event days and holidays. | `id` (PK) |
| **TimeSlot** | `TimeSlot` | Configure period timings bounds and types. | `id` (PK) |
| **Timetable** | `Timetable` | Timetable grid headers for sections. | `id` (PK) |
| **TimetableEntry** | `TimetableEntry` | Grid cell mappings binding teachers/rooms. | `id` (PK) |
| **SubstituteFaculty** | `SubstituteFaculty` | Track substitutions and swaps history. | `id` (PK) |
| **TimetableApproval** | `TimetableApproval` | Audit approvals stage workflow logs. | `id` (PK) |
| **AttendanceSession** | `AttendanceSession` | Classroom attendance sessions. | `id` (PK) |
| **AttendanceRecord** | `AttendanceRecord` | Mapped student status states (Present, Absent, etc.). | `id` (PK) |
| **AttendanceCorrection** | `AttendanceCorrection` | Student correction tickets. | `id` (PK) |
| **AttendanceAudit** | `AttendanceAudit` | Security audit trail of modifications. | `id` (PK) |
| **DefaulterList** | `DefaulterList` | Lists students with low attendance benchmarks. | `id` (PK) |
| **QRSession** | `QRSession` | Classroom locations and radius bounds. | `id` (PK), `attendanceSessionId` (UQ) |
| **QRCode** | `QRCode` | Dynamically changing encryption access keys. | `id` (PK), `codeValue` (UQ) |
| **QRScanLog** | `QRScanLog` | Scanned check-in attempts history log. | `id` (PK) |
| **GeoValidation** | `GeoValidation` | Coordinate mapping calculations log. | `id` (PK), `scanLogId` (UQ) |
| **DeviceValidation** | `DeviceValidation` | Hardware fingerprint identities log. | `id` (PK), `scanLogId` (UQ) |
| **FaceProfile** | `FaceProfile` | User biometric profiles pending admin review. | `id` (PK), `userId` (UQ) |
| **FaceEmbedding** | `FaceEmbedding` | Secure 512-dim vectors across 5 angles. | `id` (PK) |
| **FaceRegistration** | `FaceRegistration` | Historical review logs for biometrics. | `id` (PK) |
| **FaceVerification** | `FaceVerification` | Facial identification attempts. | `id` (PK) |
| **FaceAttendance** | `FaceAttendance` | Integrates face verifications with records. | `id` (PK), `attendanceRecordId` (UQ) |
| **FaceAudit** | `FaceAudit` | Audits biometric changes. | `id` (PK) |
| **LivenessCheck** | `LivenessCheck` | Records blinking yaw degree counters. | `id` (PK) |
| **SpoofDetection** | `SpoofDetection` | Anti-spoofing screen replay flags. | `id` (PK) |
| **Assignment** | `Assignment` | Assignments metadata constraints. | `id` (PK) |
| **AssignmentFile** | `AssignmentFile` | Faculty attachments uploaded. | `id` (PK) |
| **AssignmentSubmission** | `AssignmentSubmission` | Student assignment uploads. | `id` (PK), `[assignmentId, studentId]` (UQ) |
| **SubmissionAttachment** | `SubmissionAttachment` | Student submission attachments. | `id` (PK) |
| **AssignmentFeedback** | `AssignmentFeedback` | Instructor feedback and comments. | `id` (PK) |
| **AssignmentGrade** | `AssignmentGrade` | Submission marks earned. | `id` (PK), `submissionId` (UQ) |
| **AssignmentAudit** | `AssignmentAudit` | Security audit trail of assignment actions. | `id` (PK) |
| **Exam** | `Exam` | Exam metadata parameters and types. | `id` (PK) |
| **ExamSchedule** | `ExamSchedule` | Exam slot schedule assignments. | `id` (PK) |
| **ExamRoom** | `ExamRoom` | Seat layouts capacity blocks. | `id` (PK) |
| **ExamInvigilator** | `ExamInvigilator` | Assigned faculty shift details. | `id` (PK) |
| **HallTicket** | `HallTicket` | Admit cards and seat assignments. | `id` (PK), `hallTicketNumber` (UQ) |
| **SeatAllocation** | `SeatAllocation` | Mapped candidate room locations. | `id` (PK), `[blockName, roomNumber, benchNumber, seatNumber]` (UQ) |
| **QuestionPaper** | `QuestionPaper` | Uploaded versions and approval status. | `id` (PK) |
| **ExamAudit** | `ExamAudit` | Exam operations logging. | `id` (PK) |
| **Result** | `Result` | Student GPA and compiling properties. | `id` (PK), `[studentId, academicYearId, semesterNumber]` (UQ) |
| **ResultDetail** | `ResultDetail` | Subject marks details. | `id` (PK), `[resultId, subjectId]` (UQ) |
| **GradeScheme** | `GradeScheme` | Program grade scale options. | `id` (PK) |
| **GradeBoundary** | `GradeBoundary` | Letter grade cutoffs. | `id` (PK) |
| **Transcript** | `Transcript` | Grade card sheets. | `id` (PK), `qrCodeValue` (UQ) |
| **RevaluationRequest** | `RevaluationRequest` | Student photocopy/revaluation requests. | `id` (PK) |
| **ResultAnalytics** | `ResultAnalytics` | Pass percentages cached records. | `id` (PK) |
| **MeritList** | `MeritList` | Calculated rankings. | `id` (PK) |
| **ResultAudit** | `ResultAudit` | Marks audits track logs. | `id` (PK) |

---

## 🔗 Relationships & Cascades

1. **Student Cascade Rules**:
   * Deleting a student `User` cascades to delete all their profile, attendance summaries, results, assignments, certificates, documents, notifications, attendance records, correction requests, QR scan logs, biometric face profiles, assignment submissions, hall tickets, resultsCompiled, transcripts, revaluationRequests, and meritList cards.
   * Deleting a `Subject` cascades to delete all corresponding `StudentAttendanceSummary`, `StudentResult`, and `StudentAssignment` records.

2. **Faculty Cascade Rules**:
   * Deleting a faculty `User` cascades to delete their `FacultyProfile`, `AssignmentDef`, `FacultyNotes`, `FacultyQuiz`, `FacultyLeave`, `FacultyNotification`, `assignmentsCreated`, `examsCreated`, `examInvigilatorDuties`, and `revaluationApproved` records.
   * Deleting a `Subject` cascades to delete all corresponding `AssignmentDef`, `FacultyNotes`, `FacultyQuiz`, `Assignment`, `Exam`, and `ResultDetail` records.

3. **Timetable Cascade Rules**:
   * Deleting a `Timetable` cascades to delete all its entries (`TimetableEntry`) and approval logs (`TimetableApproval`).
   * Deleting a `TimeSlot` cascades to delete all mapped entries (`TimetableEntry`).
   * Deleting a `Room` or `Laboratory` sets the corresponding grid cell mappings (`roomId`, `labId`) to `NULL`.

4. **Attendance & QR Cascade Rules**:
   * Deleting an `AttendanceSession` cascades to delete its `AttendanceRecord` items, `AttendanceAudit` lines, and linked `QRSession`.
   * Deleting a `QRSession` cascades to delete all its rotating `QRCode` records, `QRScanLog` items, `GeoValidation` logs, and `DeviceValidation` parameters.

5. **Face Recognition Cascade Rules**:
   * Deleting a `FaceProfile` cascades to clear all its `FaceEmbedding` angles, `FaceVerification` items, `LivenessCheck` items, and `SpoofDetection` logs.
   * Deleting a `FaceVerification` cascades to delete its linked `FaceAttendance` bindings.

6. **Assignment Cascade Rules**:
   * Deleting an `Assignment` cascades to delete its files (`AssignmentFile`), student submissions (`AssignmentSubmission`), and audit logs (`AssignmentAudit`).
   * Deleting an `AssignmentSubmission` cascades to delete its attachments (`SubmissionAttachment`), grades (`AssignmentGrade`), and feedbacks (`AssignmentFeedback`).

7. **Exam Cascade Rules**:
   * Deleting an `Exam` cascades to delete its schedules (`ExamSchedule`), hall tickets (`HallTicket`), question papers (`QuestionPaper`), and audit logs (`ExamAudit`).
   * Deleting a `HallTicket` cascades to delete its seat allocations (`SeatAllocation`).

8. **Result Cascade Rules**:
   * Deleting a `Result` cascades to delete its child items `ResultDetail` and `ResultAudit` logs.
   * Deleting a `ResultDetail` cascades to delete its `RevaluationRequest` logs.

---

## ⚡ Index & Performance Optimizations

* **Employee ID**: Unique index on `FacultyProfile.employeeId` prevents collision.
* **FacultyProfile userId**: Unique index on `FacultyProfile.userId` links single profile cards.
* **TimeSlot Bounds**: Indices on `startTime` and `endTime` speed up overlap conflict validation check queries.
* **Grid Entry Indexing**: Combo indexes on `[dayOfWeek, timeSlotId, roomId]` and `[dayOfWeek, timeSlotId, facultyId]` speed up conflict checking lookups.
* **QR Dynamic Indexes**: Unique key index on `QRCode.codeValue` for rapid access key verification.
* **Scan log uniqueness**: Unique indexes on `GeoValidation.scanLogId` and `DeviceValidation.scanLogId` for fast join lookups.
* **Face Uniqueness Indexes**: Unique index on `FaceProfile.userId` for fast profile lookups, and unique indexes on `FaceAttendance.attendanceRecordId` and `FaceAttendance.verificationId` for one-to-one mapping queries.
* **Assignment Indexes**: Combo unique index on `[assignmentId, studentId]` in `AssignmentSubmission` speeds up student status lookups. Unique index on `AssignmentGrade.submissionId` for fast grading lookups. Index on `Assignment.dueDate` for fast sorting of upcoming deadlines.
* **Exam Indexes**: Unique index on `HallTicket.hallTicketNumber` for rapid admit check verification. Unique index on `[blockName, roomNumber, benchNumber, seatNumber]` in `SeatAllocation` ensures seat duplication prevention. Index on `Exam.examDate` speeds up overlap checking routines.
* **Result Indexes**: Combo unique index on `[studentId, academicYearId, semesterNumber]` speeds up student grade lookups. Unique index on `[resultId, subjectId]` speeds up details search. Unique index on `Transcript.qrCodeValue` for rapid validation checking. Index on `Result.cgpa` speeds up ranking sorts.

---

## 👨‍👩‍👧 Parent Portal Cascades & Indices

### Cascade Rules
- Deleting a parent `User` cascades to delete their `ParentProfile`.
- Deleting a `ParentProfile` cascades to clear all corresponding `ParentStudentLink`, `ParentNotification`, and `ParentAudit` records.
- Deleting a `User` student cascades to clear all linked `ParentStudentLink` entries.

### Indices
- Unique index on `ParentProfile.userId` for fast profile matching.
- Combo unique index on `[parentId, studentId]` in `ParentStudentLink` ensures no duplicate linking.
- Index on `ParentMessage.senderId` and `ParentMessage.receiverId` for speedier message thread queries.
- Index on `ParentNotification.parentId` and `ParentNotification.createdAt` for fast notifications display.

