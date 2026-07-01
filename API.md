# CampusGPT X - API Documentation & Integration Guide

Welcome to the CampusGPT X developer API portal. This document details the endpoints, request/response models, and security/session policies.

---

## 🔒 Authentication & Authorization

All API calls (except `/health` and `/auth/login`) require a valid JSON Web Token (JWT) provided in either the `Authorization` header or as an HTTP-only cookie.

* **Header Example**: `Authorization: Bearer <JWT_ACCESS_TOKEN>`
* **Cookie Option**: Secure HTTP-only cookie named `access_token`

---

## 📊 Standard API Response Envelope

Every endpoint returns a unified JSON envelope:

### Successful Operation
```json
{
  "success": true,
  "message": "Resource action details",
  "data": {
    "key": "value"
  },
  "errors": null
}
```

### Failed Operation
```json
{
  "success": false,
  "message": "Human-readable error details",
  "data": null,
  "errors": {
    "code": "ERROR_CODE",
    "details": {
      "field": "location",
      "issue": "specific reason"
    }
  }
}
```

---

## 🚀 API Endpoint Reference

### 1. System Health
* **Route**: `GET /api/v1/health`
* **Auth**: Public

---

### 2. Authentication
* `POST /api/v1/auth/login` - User authentication and JWT distribution.
* `POST /api/v1/auth/refresh` - Rotate access tokens using active refresh signatures.
* `POST /api/v1/auth/change-password` - Set new password keys for authenticated accounts.

---

### 3. User Directory
* `GET /api/v1/users` - Paginated and sorted active campus account directory.
* `POST /api/v1/users/import` - Bulk upload Excel sheets parsing new student/staff profiles.

---

### 4. Academic Structure Module (New in Day 4)

#### Academic Years
* `POST /api/v1/academic-years` - Create a calendar year.
* `GET /api/v1/academic-years?search=&page=1&limit=10` - List years.
* `GET /api/v1/academic-years/{id}` - Fetch single year.
* `PUT /api/v1/academic-years/{id}` - Modify properties.
* `DELETE /api/v1/academic-years/{id}` - Purge record.

#### Departments
* `POST /api/v1/departments` - Register division.
* `GET /api/v1/departments` - List departments.
* `DELETE /api/v1/departments/{id}` - Purge department (guarded against active course mappings).

#### Programs & Courses
* `POST /api/v1/programs` - Define curriculum paths (B.Tech, MBA).
* `POST /api/v1/courses` - Create course offerings (e.g. EE101).

#### Semesters & Subjects
* `POST /api/v1/semesters` - Setup semester term maps.
* `POST /api/v1/subjects` - Define syllabus details.

#### Sections
* `POST /api/v1/sections` - Add section clusters.

#### Building & Room Infrastructure
* `POST /api/v1/buildings` - Register buildings.
* `POST /api/v1/rooms` - Assign classroom and laboratory locations.

#### Laboratories
* `POST /api/v1/laboratories` - Setup multi-station research labs.

#### Faculty Timetable Assignments
* `POST /api/v1/faculty-assignments` - Assign faculty advisors/teachers to class divisions.
* **Payload**:
```json
{
  "departmentId": "dept-uuid",
  "subjectId": "subj-uuid",
  "facultyId": "user-uuid",
  "sectionId": "sect-uuid",
  "semesterId": "semester-uuid",
  "academicYearId": "academicyear-uuid"
}
```
* `DELETE /api/v1/faculty-assignments/{id}` - Remove instruction mappings.
