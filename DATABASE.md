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
5. **User Sessions, Refresh Tokens, and Login History**:
   * One-to-many relationships.
   * Cascade delete on user accounts deletes all associated sessions, logs, and tokens (`onDelete: Cascade`).

---

## ⚡ Index Optimizations

To support high performance for standard search, filtering, and authorization query operations:
* **Email & Username**: Configured indexes on `User.email` and `User.username` to optimize login credentials lookup.
* **Foreign Keys**: Managed relationships with explicit joins.
