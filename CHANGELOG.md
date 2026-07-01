# Changelog

All notable changes to the **CampusGPT X** system are logged in this file.

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
