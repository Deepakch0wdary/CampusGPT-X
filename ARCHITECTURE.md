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
   * Day 5 includes the Student Portal central control dashboard **`StudentDashboard.tsx`**.

2. **`apps/backend`**:
   * REST API engine built with **FastAPI**.
   * Day 5 registers the Student Portal endpoint handler in **`students.py`** to perform CRUD actions on student-related records.

3. **`prisma`**:
   * Relational database schema manager.

---

## 🛡️ Security Architecture

* **Broken Access Control Prevention (BACP)**:
  Every API endpoint in `students.py` reads user parameters directly from the decoded JWT token context. If the user possesses the `STUDENT` role, the backend forces `userId` queries to match `current_user.id`, ignoring arbitrary client parameters. This prevents ID enumeration attacks.
* **Audit Logging**: Saves all core state actions in the `AuditLog` database table.
