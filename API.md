# CampusGPT X - API Documentation & Integration Guide

Welcome to the CampusGPT X developer API portal. This document details the endpoints, request/response models, and security/session policies.

---

## 🔒 Authentication & Authorization

All API calls (except `/health` and `/auth/login`) require a valid JSON Web Token (JWT) provided in either the `Authorization` header or as an HTTP-only cookie.

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

---

## 🚀 API Endpoint Reference

### 1. System Health
* **Route**: `GET /api/v1/health`

---

### 2. Authentication
* `POST /api/v1/auth/login` - User authentication and JWT distribution.
* `POST /api/v1/auth/change-password` - Set new password keys for authenticated accounts.

---

### 3. User Directory
* `GET /api/v1/users` - Paginated and sorted active campus account directory.
* `POST /api/v1/users/import` - Bulk upload Excel sheets parsing new student/staff profiles.

---

### 4. Student Portal Module (New in Day 5)

#### Student Dashboard
* `GET /api/v1/student/dashboard` - Get overall attendance percentage, CGPA, completed credits, upcoming classes, timetables, and AI study recommendations.
* Optional param: `student_id` (Admins and teachers only).

#### Student Profile
* `GET /api/v1/student/profile` - Fetch current user profile.
* `PUT /api/v1/student/profile` - Update phone, emergency contact, blood group, parent details.

#### Attendance
* `GET /api/v1/student/attendance` - Subject-wise class counts and percentages.

#### Results
* `GET /api/v1/student/results` - Grades, credits weight, internal and external marks list.

#### Assignments
* `GET /api/v1/student/assignments` - Homework deadlines.
* `POST /api/v1/student/assignments/{id}/submit` - Submit link and update status.

#### Certificates
* `GET /api/v1/student/certificates` - Request listing.
* `POST /api/v1/student/certificates/request` - Triggers bonafide, study certificate requests.

#### Documents
* `GET /api/v1/student/documents` - Access digital lockers (Student IDs).

#### Notifications
* `GET /api/v1/student/notifications` - Announcements bulletins.
* `PUT /api/v1/student/notifications/{id}/read` - Mark notification as read.
