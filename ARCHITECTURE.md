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
   * Day 6 includes the Faculty Portal dashboard view **`FacultyDashboard.tsx`**.

2. **`apps/backend`**:
   * REST API engine built with **FastAPI**.
   * Day 6 registers the Faculty Portal endpoint handler in **`faculties.py`** to perform CRUD actions on faculty-related records.

3. **`prisma`**:
   * Relational database schema manager.

---

## 🛡️ Security Architecture

* **Broken Access Control Prevention (BACP)**:
  Every API endpoint in `faculties.py` reads user parameters directly from the decoded JWT token context. If the user possesses the `TEACHER` role, the backend forces subject queries to match their official `FacultyAssignment` records, preventing unauthorized editing of grades, assignments, quizzes, and classroom rosters.
* **Audit Logging**: Saves all core state actions in the `AuditLog` database table.
