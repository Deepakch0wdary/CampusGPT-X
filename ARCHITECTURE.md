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
   * Leverages proxy rules in Vite to route api traffic directly to the backend.

2. **`apps/backend`**:
   * Rest API engine built with **FastAPI**.
   * Injects database sessions explicitly using FastAPI dependencies.
   * Restricts secure endpoints with role checks (`RoleChecker`) and permission logs.

3. **`prisma`**:
   * Relational database schema manager. Maps data schemas, unique constraints, index tags, and cascading rules.

---

## 🛡️ Security Architecture

* **Cryptography**: Salted password encryption using the industry-standard **bcrypt** library.
* **Session Management**: Dual support for JWTs inside Authorization Bearer headers (typically for external/automated requests) and secure HttpOnly cookies (to prevent XSS breaches).
* **Token Rotation**: Spawns short-lived access tokens (15 mins) and long-lived refresh tokens (7 days). Refreshes invoke rotation, revoking old signatures.
* **Audit Logging**: Saves all core state actions (e.g. login failures, user creation, metadata imports) in the `AuditLog` database table.
