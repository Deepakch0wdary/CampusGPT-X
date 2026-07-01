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

### 4. Student Portal Module
* `GET /api/v1/student/dashboard` - Get overall attendance percentage, CGPA, completed credits, upcoming classes, timetables, and AI study recommendations.

---

### 5. Faculty Portal Module (New in Day 6)

#### Faculty Dashboard
* `GET /api/v1/faculty/dashboard` - Retrieve welcome cards, timetable metrics, assigned subject rosters, and pending evaluations statistics.

#### Faculty Profile
* `GET /api/v1/faculty/profile` - Fetch current user profile.
* `PUT /api/v1/faculty/profile` - Update qualifications, specialties, office hours, and emergency contact details.

#### Class Management
* `GET /api/v1/faculty/classes` - List assigned subjects, sections, and classroom strengths.
* `GET /api/v1/faculty/classes/{id}/students` - Retrieve student roster of a class section (ownership protected).

#### Assignment Management
* `POST /api/v1/faculty/assignments` - Publish an assignment template. Auto-provisions matching submissions for class students.
* `GET /api/v1/faculty/assignments` - List self-authored assignment templates.
* `GET /api/v1/faculty/assignments/{id}/submissions` - Pull student homework submission URLs and grading status.
* `DELETE /api/v1/faculty/assignments/{id}` - Revoke/Delete assignment definition.

#### Quiz Console
* `POST /api/v1/faculty/quizzes` - Publish scheduled tests with question bank JSON structures.
* `GET /api/v1/faculty/quizzes` - Retrieve self-scheduled quiz list.

#### Marks Grading Registry
* `POST /api/v1/faculty/marks/grade` - Submit grade sheets, internal marks, and external exam scores for students (ownership verified).

#### Notes Upload
* `POST /api/v1/faculty/notes` - Post reference URLs linking notes (PPT/PDF/DOCX) to courses.
* `GET /api/v1/faculty/notes` - Retrieve notes list.

#### Leave Tracker
* `POST /api/v1/faculty/leaves` - Apply for casual/sick/earned leaves.
* `GET /api/v1/faculty/leaves` - Pull leave tracking application logs.

#### Attendance Preparation
* `POST /api/v1/faculty/attendance/prepare` - Select classroom parameters and request dynamic Session ID generation headers.

#### Notifications Alerts
* `GET /api/v1/faculty/notifications` - Retrieve staff bullet alerts.
