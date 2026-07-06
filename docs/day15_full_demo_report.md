# Day 15 Full Demo & Verification Report

This document records the verification matrices, system environment, startup loops, and security guardrails for the **CampusGPT X** system.

---

## 1. System Environment & Versions

- **Node.js**: `v24.14.1`
- **npm**: `11.11.0`
- **Python**: `3.11.9`
- **Git**: `2.54.0.windows.1`
- **Database Status**: Local Port `3306` (Offline/Blocked). Real database operation has been bypassed or mocked in favor of unit/integration test engines.
- **Vite Port**: `5174` (Port `5173` occupied by a background process, auto-shifted).

---

## 2. Verification Matrices

### 2.1 API Smoke Test Matrix
The `demo_smoke_test.py` script queried the active local backend loop:

| Endpoint | Method | Expected HTTP | Actual HTTP | Result |
| :--- | :--- | :--- | :--- | :--- |
| `/api/v1/health` | `GET` | 200 | 200 | **PASS** |
| `/docs` | `GET` | 200 | 200 | **PASS** |
| `/api/v1/admissions` | `GET` | 401 / 403 | 401 | **PASS** |

### 2.2 Pytest Integration Regression Suite
- **Total Tests**: 55
- **Passed**: 55
- **Failed**: 0
- **Duration**: ~24.33 seconds
- **Status**: **100% SUCCESS**

### 2.3 Browser E2E Test Matrix
An automated browser subagent executed page load checks on `http://localhost:5174/`:

| Step Description | Element Target | Verified State | Result |
| :--- | :--- | :--- | :--- |
| **Open Page** | `http://localhost:5174/` | Status 200 Page Loaded | **PASS** |
| **Header Check** | `Typography` | Text "CampusGPT X" visible | **PASS** |
| **Email field check** | `input[type="text"]` | Inputs render successfully | **PASS** |
| **Password field check** | `input[type="password"]` | Inputs render successfully | **PASS** |
| **Screenshot captured** | saved artifact | File saved successfully | **PASS** |

---

## 3. Demo Accounts & Role Permissions Configuration

Identities seeded dynamically:

1. **Master Admin**: `admin.demo@campusgpt.local`
2. **Admission Officer**: `admission.demo@campusgpt.local`
3. **Finance Officer**: `finance.demo@campusgpt.local`
4. **Teacher / Instructor**: `teacher.demo@campusgpt.local`
5. **Student**: `student.demo@campusgpt.local`
6. **Parent**: `parent.demo@campusgpt.local`

### Role-Based Access Controls (RBAC) Verified:
- **Student**: Denied access to admin portals and grading handlers. Restructured timetable searches to filter by student's active `sectionId`.
- **Teacher**: Restricted to assigned subject rosters and manual/QR attendance inputs.
- **Parent**: Direct student profile, result cards, and billing indicators.
- **Parent IDOR Security Check**: BACP checks reject queries for unlinked students with a secure `403 Forbidden` response.

---

## 4. Workflows Accomplished

### 4.1 Admission & Fee Management
- **Enrollment**: Generates unique candidate numbers upon officer approval.
- **Fee structures**: Net invoice computation stackings with scholarship overrides.
- **Idempotency**: Prevents double payment ledger updates via idempotency token locks.

### 4.2 Parent Portal
- **Dashboard**: Switches student views cleanly via active select widgets.
- **Messaging**: Integrated direct parent-to-faculty feed.
- **Notifications**: Delivers low attendance warning banners (< 75% thresholds).

---

## 5. Known Limitations
- Since local MySQL database engine port 3306 is not active, runtime database actions on live browsers will report operational errors. However, all backend endpoint logic compiles and is verified by the SQLite in-memory test runner.

---

## 6. Running Local URLs

- **Frontend Application**: [http://localhost:5174/](http://localhost:5174/)
- **Backend Application**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Swagger Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health API Endpoint**: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)
