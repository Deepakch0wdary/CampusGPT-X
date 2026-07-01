# CampusGPT X - API Documentation & Integration Guide

Welcome to the CampusGPT X developer API portal. This document details the endpoints, request/response models, and security/session policies.

---

## 🔒 Authentication & Authorization

All API calls (except `/health` and `/auth/login`) require a valid JSON Web Token (JWT) provided in either the `Authorization` header or as an HTTP-only cookie.

* **Header Example**: `Authorization: Bearer <JWT_ACCESS_TOKEN>`
* **Cookie Option**: Secure HTTP-only cookie named `access_token`

### Security Checks
1. **Password Expiry**: If `mustChangePassword` is `true`, calls to non-auth routes will return `403 Forbidden` with detail `"First-time login: Password change is required."`.
2. **RBAC Guarding**: Endpoints verify permissions using `RoleChecker` and `PermissionChecker`.

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
* **Response**:
```json
{
  "success": true,
  "message": "System health status.",
  "data": {
    "status": "healthy",
    "timestamp": 1782899226.12,
    "api": {
      "status": "healthy",
      "latency_ms": 12.5
    },
    "database": {
      "status": "healthy",
      "latency_ms": 5.2
    }
  },
  "errors": null
}
```

### 2. Authentication

#### User Login
* **Route**: `POST /api/v1/auth/login`
* **Payload**:
```json
{
  "username_or_email": "admin",
  "password": "AdminPassword@123"
}
```
* **Response**:
```json
{
  "success": true,
  "message": "Login successful.",
  "data": {
    "access_token": "eyJhbGciOi...",
    "refresh_token": "eyJhbGciOi...",
    "must_change_password": false,
    "user": {
      "id": "80f7e72f-afa3-495f-9fbf-b9afcbff1f6f",
      "email": "admin@campusgpt.com",
      "username": "admin",
      "name": "Master Admin",
      "role": "MASTER_ADMIN"
    }
  },
  "errors": null
}
```

#### Token Rotation / Refresh
* **Route**: `POST /api/v1/auth/refresh`
* **Headers**: `Authorization: Bearer <REFRESH_TOKEN>`
* **Response**:
```json
{
  "success": true,
  "message": "Token refreshed successfully.",
  "data": {
    "access_token": "new_access_token_jwt",
    "refresh_token": "new_refresh_token_jwt"
  },
  "errors": null
}
```

#### Change Password
* **Route**: `POST /api/v1/auth/change-password`
* **Payload**:
```json
{
  "current_password": "AdminPassword@123",
  "new_password": "NewSecurePassword@123"
}
```

---

### 3. User Directory

#### List Users (Paginated & Sorted)
* **Route**: `GET /api/v1/users?page=1&limit=10&sort_by=name&sort_order=asc`
* **Permissions**: `users:read`
* **Response**:
```json
{
  "success": true,
  "message": "Users listed successfully.",
  "data": {
    "users": [
      {
        "id": "80f7e72f-...",
        "email": "student@campusgpt.com",
        "username": "student1",
        "name": "Alice Student",
        "role": "STUDENT",
        "status": "ACTIVE",
        "createdAt": "2026-07-01T12:00:00"
      }
    ],
    "total": 1,
    "page": 1,
    "pages": 1
  },
  "errors": null
}
```

#### Bulk Import Excel
* **Route**: `POST /api/v1/users/import`
* **Payload**: multipart/form-data with file upload field `file`
* **Permissions**: `users:create`
* **Response**:
```json
{
  "success": true,
  "message": "Import completed. Imported: 2.",
  "data": {
    "imported": 2,
    "errors": []
  },
  "errors": null
}
```
