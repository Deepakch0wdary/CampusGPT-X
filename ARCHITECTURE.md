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
   * Day 4 includes the interactive admin and teacher central navigation pane **`AcademicDashboard.tsx`**.

2. **`apps/backend`**:
   * REST API engine built with **FastAPI**.
   * Day 4 registers 11 new REST routers under **`academics.py`** to perform CRUD actions on structural elements.
   * Explicit dependency injection of transactional sessions using `get_db` dependencies.

3. **`prisma`**:
   * Relational database schema manager. Maps data schemas, unique constraints, index tags, and cascading rules.

---

## 🛡️ Security Architecture

* **Cryptography**: Salted password encryption using the industry-standard **bcrypt** library.
* **Session Management**: Dual support for JWTs inside Authorization Bearer headers (typically for external/automated requests) and secure HttpOnly cookies (to prevent XSS breaches).
* **Token Rotation**: Spawns short-lived access tokens (15 mins) and long-lived refresh tokens (7 days). Refreshes invoke rotation, revoking old signatures.
* **Audit Logging**: Saves all core state actions (e.g. login failures, user creation, metadata imports, academic record modifications) in the `AuditLog` database table.
