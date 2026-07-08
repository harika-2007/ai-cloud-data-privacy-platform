# API Reference

Base URL: `http://localhost:8000/api/v1`

---

## Table of Contents

1. [Authentication](#1-authentication)
2. [Files](#2-files)
3. [Scans](#3-scans)
4. [AI](#4-ai)
5. [Dashboard](#5-dashboard)
6. [Alerts](#6-alerts)
7. [Reports](#7-reports)
8. [Users](#8-users)
9. [Health](#9-health)

---

## Authentication

All endpoints except `/auth/register`, `/auth/login`, `/auth/google-login`, and `/health` require JWT authentication. Include the access token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

Access tokens expire after 15 minutes. Use the `/auth/refresh` endpoint with your refresh token to obtain new tokens.

### POST /auth/register

Register a new user account. Returns JWT tokens on success.

**Rate Limit:** 5 requests per minute per IP

**Request Body:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "Secure@123"
}
```

**Validation Rules:**
| Field | Rule |
|-------|------|
| `name` | Required, 2-100 characters |
| `email` | Required, valid email format |
| `password` | Required, 8-128 chars, must contain uppercase, lowercase, number |

**Response:** `201 Created`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "name": "John Doe",
    "email": "john@example.com",
    "role": "user",
    "is_active": true,
    "provider": "LOCAL",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

**Error Responses:**
| Status | Description |
|--------|-------------|
| `409 Conflict` | Email already registered |
| `422 Unprocessable Entity` | Validation error |

---

### POST /auth/login

Authenticate with email and password.

**Rate Limit:** 10 requests per minute per IP

**Request Body:**
```json
{
  "email": "john@example.com",
  "password": "Secure@123"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "name": "John Doe",
    "email": "john@example.com",
    "role": "user",
    "is_active": true,
    "provider": "LOCAL",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

---

### POST /auth/google-login

Authenticate with Google Sign-In using a Google ID token.

**Request Body:**
```json
{
  "credential": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjEyMzQ1Njc4OTAiLCJ0eXAiOiJKV1QifQ..."
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "name": "John Doe",
    "email": "john@gmail.com",
    "role": "user",
    "is_active": true,
    "provider": "GOOGLE",
    "google_id": "1234567890",
    "profile_picture": "https://lh3.googleusercontent.com/a/...",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

---

### POST /auth/refresh

Obtain new tokens using a valid refresh token.

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

---

### GET /auth/me

Get the currently authenticated user's profile.

**Response:** `200 OK`
```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "name": "John Doe",
  "email": "john@example.com",
  "role": "user",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "last_login": "2024-01-15T10:30:00Z",
  "file_count": 12,
  "scan_count": 8
}
```

---

### PUT /auth/me

Update user profile. To change password, provide both `current_password` and `new_password`.

**Request Body:**
```json
{
  "name": "John Updated",
  "current_password": "Secure@123",
  "new_password": "NewSecure@456"
}
```

---

## 2. Files

### POST /files/upload

Upload a file for PII scanning. Supported types: CSV, XLSX, PDF, TXT. Max size: 50 MB.

**Request (multipart/form-data):**
| Field | Type | Description |
|-------|------|-------------|
| `file` | File | File to upload (max 50MB) |

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/v1/files/upload \
  -H "Authorization: Bearer <access_token>" \
  -F "file=@/path/to/data.csv"
```

**Response:** `201 Created`
```json
{
  "id": "a1b2c3d4-1234-5678-9abc-def012345678",
  "filename": "data.csv",
  "original_filename": "customer_data.csv",
  "file_size": 245760,
  "file_type": "csv",
  "status": "uploaded",
  "uploaded_at": "2024-01-15T10:30:00Z",
  "user_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
}
```

---

### GET /files

List all files for the authenticated user. Supports pagination and filtering.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `skip` | integer | 0 | Records to skip |
| `limit` | integer | 20 | Max per page (max 100) |
| `status` | string | - | Filter: `uploaded`, `scanning`, `scanned`, `failed` |
| `file_type` | string | - | Filter: `csv`, `xlsx`, `pdf`, `txt` |
| `search` | string | - | Search by filename |

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "a1b2c3d4-1234-5678-9abc-def012345678",
      "filename": "customer_data.csv",
      "file_size": 245760,
      "file_type": "csv",
      "status": "scanned",
      "uploaded_at": "2024-01-15T10:30:00Z",
      "risk_score": 85,
      "risk_level": "HIGH",
      "findings_count": 15
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 20,
  "total_pages": 3
}
```

---

### GET /files/{id}

Get detailed information about a specific file.

**Response:** `200 OK`
```json
{
  "id": "a1b2c3d4-1234-5678-9abc-def012345678",
  "filename": "customer_data.csv",
  "file_size": 245760,
  "file_type": "csv",
  "status": "scanned",
  "uploaded_at": "2024-01-15T10:30:00Z",
  "risk_assessment": {
    "risk_score": 85,
    "risk_level": "HIGH",
    "findings_count": 15,
    "findings_breakdown": {
      "aadhaar": 3, "pan": 5, "credit_card": 2, "email": 3, "phone": 2
    }
  }
}
```

---

### DELETE /files/{id}

Delete a file and its associated data. **Response:** `204 No Content`

---

## 3. Scans

### POST /scans/start/{file_id}

Start a PII scan on a file. Returns immediately.

**Response:** `202 Accepted`
```json
{
  "scan_id": "b2c3d4e5-2345-6789-0abc-def012345679",
  "file_id": "a1b2c3d4-1234-5678-9abc-def012345678",
  "status": "in_progress",
  "started_at": "2024-01-15T10:30:45Z"
}
```

---

### GET /scans/file/{file_id}

Get scan results with all PII findings.

**Response:** `200 OK`
```json
{
  "file_id": "a1b2c3d4-1234-5678-9abc-def012345678",
  "total_findings": 15,
  "scan_status": "completed",
  "findings": [
    {
      "id": "c3d4e5f6-3456-7890-0abc-def01234567a",
      "pii_type": "aadhaar",
      "value": "XXXX-XXXX-1234",
      "confidence": 0.98,
      "severity": "critical",
      "line_number": 42
    }
  ],
  "risk_assessment": {
    "risk_score": 85,
    "risk_level": "HIGH"
  }
}
```

---

### GET /scans/risk/file/{file_id}

Get only the risk assessment.

**Response:** `200 OK`
```json
{
  "file_id": "a1b2c3d4-1234-5678-9abc-def012345678",
  "risk_score": 85,
  "risk_level": "HIGH",
  "findings_count": 15
}
```

---

## 4. AI

### POST /ai/recommend/{file_id}

Generate AI compliance recommendations.

**Response:** `200 OK`
```json
{
  "file_id": "a1b2c3d4-1234-5678-9abc-def012345678",
  "model": "llama3",
  "recommendations": [
    {
      "pii_type": "aadhaar",
      "finding": "3 Aadhaar numbers detected",
      "recommendation": "Mask first 8 digits. Use tokenization.",
      "priority": "high"
    },
    {
      "pii_type": "credit_card",
      "finding": "2 credit card numbers detected",
      "recommendation": "Isolate data. Use PCI DSS compliant storage.",
      "priority": "critical"
    }
  ]
}
```

---

### POST /ai/summary/{file_id}

Generate executive summary.

**Response:** `200 OK`
```json
{
  "file_id": "a1b2c3d4-1234-5678-9abc-def012345678",
  "executive_summary": "File contains 15 PII findings. Risk score: 85 (HIGH).",
  "compliance_status": "non_compliant",
  "affected_regulations": ["IT Act 2000", "Aadhaar Act 2016", "PCI DSS"]
}
```

---

### POST /ai/chat

Chat with the AI assistant.

**Request Body:**
```json
{
  "message": "Best practices for storing Aadhaar data?",
  "context_file_id": "a1b2c3d4-1234-5678-9abc-def012345678"
}
```

**Response:** `200 OK`
```json
{
  "reply": "Best practices include: masking, encryption, access control, audit logging, and data minimization per Aadhaar Act 2016.",
  "model": "llama3"
}
```

---

## 5. Dashboard

### GET /dashboard/stats

Get overall dashboard statistics.

**Response:** `200 OK`
```json
{
  "total_files": 42,
  "total_scanned": 38,
  "total_findings": 320,
  "high_risk_files": 12,
  "total_alerts": 28,
  "unread_alerts": 5,
  "overall_risk_score": 65,
  "compliance_score": 72.5
}
```

---

### GET /dashboard/trends

Get trend data for charts.

**Query Parameters:** `period` (`24h`, `7d`, `30d`, `90d`; default `7d`)

**Response:** `200 OK`
```json
{
  "scan_trends": [
    {"date": "2024-01-09", "files_scanned": 3, "findings_found": 25}
  ],
  "risk_distribution": { "HIGH": 12, "MEDIUM": 15, "LOW": 11 },
  "pii_type_distribution": { "aadhaar": 45, "pan": 68, "email": 112 }
}
```

---

### GET /dashboard/full

Get complete dashboard data (stats + trends combined).

---

## 6. Alerts

### GET /alerts

List alerts. Supports pagination and filtering.

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "d4e5f6a7-4567-8901-0abc-def01234567b",
      "type": "risk_threshold",
      "severity": "critical",
      "title": "High Risk File Detected",
      "message": "Risk score of 85 (HIGH)",
      "is_read": false,
      "created_at": "2024-01-15T10:31:15Z"
    }
  ],
  "total": 28,
  "unread_count": 5
}
```

---

### GET /alerts/stats

Get alert statistics.

**Response:** `200 OK`
```json
{
  "total": 28,
  "unread": 5,
  "by_severity": { "critical": 3, "high": 8, "medium": 12, "low": 5 }
}
```

---

### PUT /alerts/{id}/read

Mark alert as read. **Response:** `200 OK`
```json
{ "id": "...", "is_read": true, "read_at": "2024-01-15T11:00:00Z" }
```

### PUT /alerts/read-all

Mark all alerts as read. **Response:** `200 OK`
```json
{ "success": true, "marked_read": 12 }
```

---

## 7. Reports

### POST /reports/generate

Generate a PDF report.

**Request Body:**
```json
{
  "file_id": "a1b2c3d4-1234-5678-9abc-def012345678",
  "include_ai_recommendations": true,
  "format": "pdf"
}
```

**Response:** `202 Accepted`
```json
{ "report_id": "e5f6a7b8-5678-9012-0abc-def01234567c", "status": "generating" }
```

---

### GET /reports

List reports. **Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "e5f6a7b8-5678-9012-0abc-def01234567c",
      "file_name": "customer_data.csv",
      "status": "completed",
      "generated_at": "2024-01-15T10:35:15Z"
    }
  ],
  "total": 15
}
```

### GET /reports/{id}/download

Download PDF.

---

## 8. Users

Requires `admin` or `analyst` role.

### GET /users

List all users. **Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "name": "John Doe",
      "email": "john@example.com",
      "role": "user",
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 25
}
```

### GET /users/{id} / PUT /users/{id}/role / DELETE /users/{id}

Get, update role, or deactivate a user.

---

## 9. Health

### GET /health

Public health check. **Response:** `200 OK`
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "database": { "status": "healthy" },
    "ollama": { "status": "healthy", "model": "llama3" }
  }
}
```

---

## Error Handling

```json
{
  "detail": {
    "code": "VALIDATION_ERROR",
    "message": "Error description",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 202 | Accepted |
| 204 | No Content |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 409 | Conflict |
| 413 | Payload Too Large |
| 422 | Unprocessable Entity |
| 429 | Too Many Requests |
| 500 | Internal Server Error |

### Rate Limits

| Group | Limit |
|-------|-------|
| Auth | 10 req/min |
| Register | 5 req/min |
| File upload | 20 req/min |
| AI | 30 req/min |
| Other | 60 req/min |
