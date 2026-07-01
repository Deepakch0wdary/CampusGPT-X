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

---

## 🔗 Relationships & Cascades

1. **Student Cascade Rules**:
   * Deleting a student `User` cascades to delete all their profile, attendance summaries, results, assignments, certificates, documents, and notifications.
   * Deleting a `Subject` cascades to delete all corresponding `StudentAttendanceSummary`, `StudentResult`, and `StudentAssignment` records.

2. **Faculty Cascade Rules**:
   * Deleting a faculty `User` cascades to delete their `FacultyProfile`, `AssignmentDef`, `FacultyNotes`, `FacultyQuiz`, `FacultyLeave`, and `FacultyNotification` records.
   * Deleting a `Subject` cascades to delete all corresponding `AssignmentDef`, `FacultyNotes`, and `FacultyQuiz` records.

---

## ⚡ Index & Performance Optimizations

* **Employee ID**: Unique index on `FacultyProfile.employeeId` prevents collision.
* **FacultyProfile userId**: Unique index on `FacultyProfile.userId` links single profile cards.
