# Changelog

All notable changes to the **CampusGPT X** system are logged in this file.

---

## [4.0-Complete] - 2026-07-01
### Added
* Complete Academic Structure Module including:
  * **Academic Year**: Start/End dates, Current Academic Year toggles.
  * **Department**: Codes, deanHod name fields.
  * **Program**: Curriculums mapping (B.Tech, M.Tech, MBA, MCA, BCA, custom).
  * **Course**: Course codes, credits, durations.
  * **Semester**: Start/End dates, current semesters toggles.
  * **Subject**: theory/lab hours, elective vs. mandatory markers.
  * **Section**: Classroom section divisions and capacities.
  * **Buildings & Rooms**: Infrastructure mapping, seat capacity, AC, Projector indicators.
  * **Laboratories**: Systems count and software environments.
  * **Faculty Assignment**: Administrative workflow maps connecting department, subjects, sections, and semesters to instructors.
* Interactive high-fidelity React `AcademicDashboard.tsx` view with tab panels and modal dialogs.
* Business validation layer preventing duplicates and active entity deletions.

---

## [3.5-Stable] - 2026-07-01
### Added
* Custom error boundary views for:
  * **404 Not Found Page** (`NotFound.tsx`)
  * **403 Forbidden Access Page** (`Forbidden.tsx`)
  * **500 Server Error Page** (`ServerError.tsx`)
* Form validation guards and clear visual loading and skeleton states.
* Unified API standard helper (`make_response`) inside the backend core module.

### Refactored & Standardized
* Standardized all API routes (`health`, `auth`, `users`, `sessions`, `audits`) to output a consistent JSON envelope structure:
```json
{
  "success": true/false,
  "message": "Action summary...",
  "data": {},
  "errors": null
}
```
* Exception handling standardized to return standard error structures with error code mapping.
* Backwards compatibility maintained for current test assertions.

### Fixed
* Unused imports and unused variable warnings in the codebase.
* Addressed `errors` validation response shape mapping in the standard seeder.

---

## [3.0] - 2026-06-30
### Added
* Completed User and Profile Directory.
* Added support for bulk accounts import and export via Excel spreadsheet matrices.
* Configured role checks and restrictions ensuring `MASTER_ADMIN` count limit = 1.
