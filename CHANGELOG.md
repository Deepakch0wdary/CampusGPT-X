# Changelog

All notable changes to the **CampusGPT X** system are logged in this file.

---

## [8.0-Complete] - 2026-07-01
### Added
* Complete Attendance Management System including:
  * **Attendance Sessions**: Track classroom sessions by academic parameters and timings.
  * **Manual / Batch Attendance marking**: Easily mark students as Present, Absent, Late, Medical Leave, or On Duty on a section roster list grid.
  * **Dynamic percentage recalculation**: Recalculates `StudentAttendanceSummary` parameters upon closing/finalizing sessions.
  * **Automated Defaulter lists**: Defaulter lists generated for students dropping below 75%, 65%, or 50% benchmarks.
  * **Resolution requests workflows**: Student correction tickets reviewed, verified, and commented on by instructors.
  * **Security & Audit traces**: Log operations, origin IPs, device user-agents, and modification reasons.
* Fully interactive React `AttendanceDashboard.tsx` view with roster grids, defaulter searches, and correction review modals.

---

## [7.0-Complete] - 2026-07-01
### Added
* Complete Smart Timetable Management Module including:
  * **Academic Calendars**: Track holidays, events, and special working days.
  * **Period/Time Slot configurations**: Setup period bounds and breaks with validation preventing overlaps.
  * **Automatic Conflict Detection Checks**: Automated verification of faculty clashes, room occupied states, laboratory clashes, and student duplicate period maps.
  * **Substitute Faculty Coordinator desk**: Swap teachers for classes on selected dates, track history logs, and manage admin approvals.
  * **Multi-Stage Approval Workflow**: Move grids from Draft -> Department -> Academic Office -> Master Admin published status.
  * **Role-Specific grid schedules**: Custom weekly and daily schedules loaded for students and faculty.
* Highly responsive React `TimetableDashboard.tsx` with weekly timetable matrix editor and modal dialogs.

---

## [6.0-Complete] - 2026-07-01
### Added
* Complete Faculty Portal and Faculty Dashboard Module including:
  * **Faculty Profile metadata**: Track employee id, qualification, office location, experience, specializations, office hours, and emergency contact parameters.
  * **Faculty Dashboard widgets**: Display welcome card, dynamic weekly timetables, subjects/sections count assigned, and pending submissions counts requiring evaluation.
  * **Classroom Management**: Check student lists belonging to assigned sections.
  * **Assignment definitions manager**: Create assignments definition sheets, set deadlines, and configure resubmission allowances.
  * **Quiz scheduler module**: Question bank schemas supporting MCQs, programming, and subjective lists.
  * **Notes / Resources Archive**: Share/Publish PPT/PDF/DOCX resources linked to courses.
  * **Leaves request module**: Request sick/casual leaves and track status approvals.
  * **Attendance Session Generator**: Select Department, Semester, Section, Subject, Date, and Period. Generates a session ID header.
* Fully interactive React `FacultyDashboard.tsx` view with tab panels and modal submit forms.
* Broken Access Control Prevention validation checks in the backend protecting class rosters, note uploads, and student grading sheets from unauthorized users.

---

## [5.0-Complete] - 2026-07-01
### Added
* Complete Student Portal and Student Dashboard Module including:
  * **Student Profile metadata**: Added unique USN, parent contact details, emergency details, and blood group fields.
  * **Student Dashboard widgets**: Track overall attendance ratios, GPAs, completed credits, pending assignments, fee status, and AI study recommendations.
  * **Attendance Tracker**: Subject-wise class counting and shortage safety indicators.
  * **Academic Results**: Internals/Externals grade card breakdown and GPA calculators.
  * **Assignment Submissions**: Student submission link uploads, late sub warnings, and grading status.
  * **Certificate Requests**: Request bonafide, study, or fee receipts PDFs.
  * **Official Documents**: Digital archives (Student ID, Admission Letters).
  * **Notifications Alerting**: Broadcast announcements and placements bulletins.
* Interactive high-fidelity React `StudentDashboard.tsx` view with tab panels and modal submit fields.
* Business authorization validation preventing BOLA, URL tampering, and unauthorized data inspections.

---

## [4.0-Complete] - 2026-07-01
### Added
* Complete Academic Structure Module including:
  * **Academic Year**: Start/End dates, Current Academic Year toggles.
  * **Department**: Codes, deanHod name fields.
  * **Program**: Curriculums mapping (B.Tech, M.Tech, MBA, MCA, BCA, custom).
  * **Course**: Course codes, credits, durations.
  * **Semester**: Start/End dates, current semesters toggles.
  * **Subject**: theory/lab hours, elective vs. mandatory markers.
  * **Section**: Classroom section divisions and capacities.
  * **Buildings & Rooms**: Infrastructure mapping, seat capacity, AC, Projector indicators.
  * **Laboratories**: Systems count and software environments.
  * **Faculty Assignment**: Administrative workflow maps connecting department, subjects, sections, and semesters to instructors.
* Interactive high-fidelity React `AcademicDashboard.tsx` view with tab panels and modal dialogs.
* Business validation layer preventing duplicates and active entity deletions.

---

## [3.5-Stable] - 2026-07-01
### Added
* Custom error boundary views for:
  * **404 Not Found Page** (`NotFound.tsx`)
  * **403 Forbidden Access Page** (`Forbidden.tsx`)
  * **500 Server Error Page** (`ServerError.tsx`)
* Form validation guards and clear visual loading and skeleton states.
* Unified API standard helper (`make_response`) inside the backend core module.

### Refactored & Standardized
* Standardized all API routes (`health`, `auth`, `users`, `sessions`, `audits`) to output a consistent JSON envelope structure:
```json
{
  "success": true/false,
  "message": "Action summary...",
  "data": {},
  "errors": null
}
```
* Exception handling standardized to return standard error structures with error code mapping.
* Backwards compatibility maintained for current test assertions.

### Fixed
* Unused imports and unused variable warnings in the codebase.
* Addressed `errors` validation response shape mapping in the standard seeder.

---

## [3.0] - 2026-06-30
### Added
* Completed User and Profile Directory.
* Added support for bulk accounts import and export via Excel spreadsheet matrices.
* Configured role checks and restrictions ensuring `MASTER_ADMIN` count limit = 1.
