# CampusGPT X - Database Schema Documentation

This document describes the database design, tables, relations, and optimization indexes implemented in **CampusGPT X**.

---

## 🗄️ Database Tables Overview

| Model | Table Name | Purpose | Primary / Unique Keys |
|---|---|---|---|
| **User** | `User` | Stores all core user login identity profiles. | `id` (PK), `email` (UQ), `username` (UQ) |
| **Role** | `Role` | System roles (e.g. MASTER_ADMIN, STUDENT). | `id` (PK), `name` (UQ) |
| **Permission** | `Permission` | Action capabilities (e.g. users:read, audits:read). | `id` (PK), `name` (UQ) |
| **UserPermission** | `UserPermission` | Custom direct RBAC permission bindings. | `id` (PK), `[userId, permissionId]` (UQ) |
| **UserSession** | `UserSession` | Track active device session logs. | `id` (PK) |
| **RefreshToken** | `RefreshToken` | Retain active JWT refresh tokens. | `id` (PK), `token` (UQ) |
| **LoginHistory** | `LoginHistory` | Audit trail of log attempts and lockdowns. | `id` (PK) |
| **AuditLog** | `AuditLog` | Track state changes and transactions. | `id` (PK) |
| **UserProfile** | `UserProfile` | User metadata (phone, bio, address). | `id` (PK), `userId` (UQ) |
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

---

## 🔗 Relationships & Cascades

1. **User ↔ Role**:
   * One-to-many relationship. A user must belong to exactly one role.
   * `User.roleId` references `Role.id`.
2. **User ↔ Department**:
   * Optional relationship.
   * `User.departmentId` references `Department.id` with `onDelete: SetNull`.
3. **User ↔ Section**:
   * Optional relationship.
   * `User.sectionId` references `Section.id` with `onDelete: SetNull`.
4. **User ↔ UserProfile**:
   * One-to-one relationship.
   * `UserProfile.userId` references `User.id` with `onDelete: Cascade`.
5. **Academic Structure Cascading Hierarchy**:
   * Deleting a `Department` cascades to delete all its `Program` mappings.
   * Deleting a `Program` cascades to delete all its `Course` and `Semester` divisions.
   * Deleting a `Semester` cascades to delete all its `Section` and `Subject` entries.
   * Deleting a `Building` cascades to delete all its nested `Room` locations.
6. **FacultyAssignment Constraints**:
   * Referencing department, subjects, sections, and semesters features `onDelete: Cascade` rules to prevent orphaned schedule records.

---

## ⚡ Index & Performance Optimizations

* **Email & Username**: Configured indexes on `User.email` and `User.username` to optimize login credentials lookup.
* **FacultyAssignment Unique Combo Index**: Unique index on `[facultyId, subjectId, sectionId, semesterId, academicYearId]` speeds up timetable conflict checks and enforces mapping integrity.
