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

2. **`apps/backend`**:
   * REST API engine built with **FastAPI**.
   * Day 7 registers the Smart Timetable endpoint handler in **`timetables.py`** to perform CRUD actions and conflict detection checks.

3. **`prisma`**:
   * Relational database schema manager.

---

## 🛡️ Security Architecture

* **Broken Access Control Prevention (BACP)**:
  Every API endpoint in `timetables.py` reads user parameters directly from the decoded JWT token context. Timetable grid modifications and slot mapping creations are strictly restricted to `MASTER_ADMIN` roles. Student role scheduled queries automatically filter results by their active `sectionId` in their profiles, preventing arbitrary ID parameter query inspection.
* **Audit Logging**: Saves all core state actions in the `AuditLog` database table.
