# CampusGPT X - Architecture Documentation

This document describes the services, design patterns, and engineering paradigms of **CampusGPT X**.

---

## 🏗️ Services Architecture

CampusGPT X is built as a high-performance monorepo:

```
                      +-------------------+
                      |   React Frontend  |
                      |   (Vite + TS)     |
                      +---------+---------+
                                |
                                | HTTP JSON Rest APIs
                                v
                      +-------------------+
                      |   FastAPI Backend |
                      +---------+---------+
                                |
                                | SQLAlchemy ORM
                                v
                      +-------------------+
                      |   MySQL Database  |
                      |  (Prisma Schema)  |
                      +-------------------+
```

1. **`apps/frontend`**:
   * Single Page Application (SPA) utilizing **React 18**, **Vite**, **TypeScript**, and **Tailwind CSS**.
   * Responsive interfaces crafted with **Material UI (MUI)**.
   * Day 7 includes the Smart Timetable dashboard view **`TimetableDashboard.tsx`**.
   * Day 8 includes the Attendance Management console view **`AttendanceDashboard.tsx`**.
   * Day 9 includes the Dynamic QR Attendance dashboard view **`QRAttendanceDashboard.tsx`**.
   * Day 10 includes the Face Recognition dashboard view **`FaceRecognitionDashboard.tsx`**.
   * Day 11 includes the Assignment Management dashboard view **`AssignmentDashboard.tsx`**.
   * Day 12 includes the Examination Management dashboard view **`ExamDashboard.tsx`**.

2. **`apps/backend`**:
   * REST API engine built with **FastAPI**.
   * Day 7 registers the Smart Timetable endpoint handler in **`timetables.py`** to perform CRUD actions and conflict detection checks.
   * Day 8 registers the Attendance Management endpoint handler in **`attendances.py`** to handle session mark lists, auto-recalculations, and defaulters.
   * Day 9 registers the Dynamic QR Attendance endpoint handler in **`qr_attendances.py`** to perform geofence calculations, token rotation, and device checks.
   * Day 10 registers the Face Recognition endpoint handler in **`faces.py`** to handle biometric registrations, liveness metrics, anti-spoof checks, and reviews.
   * Day 11 registers the Assignment Management endpoint handler in **`assignments.py`** to handle CRUD, student uploads, resubmissions, and grades.
   * Day 12 registers the Examination Management endpoint handler in **`exams.py`** to handle CRUD, scheduling conflict check routines, and seat allocation parameters.

3. **`prisma`**:
   * Relational database schema manager.

---

## 🛡️ Security Architecture

* **Broken Access Control Prevention (BACP)**:
  Every API endpoint in `timetables.py` reads user parameters directly from the decoded JWT token context. Timetable grid modifications and slot mapping creations are strictly restricted to `MASTER_ADMIN` roles. Student role scheduled queries automatically filter results by their active `sectionId` in their profiles, preventing arbitrary ID parameter query inspection.
* **Audit Logging**: Saves all core state actions in the `AuditLog` database table.
