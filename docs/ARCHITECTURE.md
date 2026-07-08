# Architecture Guide

> **AI-Powered Cloud Data Privacy Compliance & Security Monitoring Platform**

---

## Table of Contents

1. [System Architecture Overview](#1-system-architecture-overview)
2. [Frontend Architecture](#2-frontend-architecture)
3. [Backend Architecture](#3-backend-architecture)
4. [Database Schema and Relationships](#4-database-schema-and-relationships)
5. [Authentication Flow](#5-authentication-flow)
6. [PII Detection Pipeline](#6-pii-detection-pipeline)
7. [AI Integration](#7-ai-integration)
8. [Security Architecture](#8-security-architecture)
9. [Deployment Architecture](#9-deployment-architecture)

---

## 1. System Architecture Overview

The platform follows a **clean architecture** pattern with clear separation of concerns across four layers:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Frontend (React + Vite)                         │
│  ┌─────────┐ ┌──────────┐ ┌───────────┐ ┌──────────┐ ┌──────────────┐ │
│  │  Auth   │ │ Dashboard│ │   Scan    │ │ Reports  │ │   AI Chat    │ │
│  │  Pages  │ │  Widgets │ │  Results  │ │  Table   │ │  Assistant   │ │
│  └────┬────┘ └────┬─────┘ └─────┬─────┘ └────┬─────┘ └──────┬───────┘ │
│       └───────────┴─────────────┴────────────┴──────────────┘          │
│                            Axios API Client                             │
│                        (JWT interceptor + refresh)                      │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │ HTTP / HTTPS
                                 │ /api/v1/*
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    Reverse Proxy (Nginx)                                │
│              (Load balancing, SSL termination, static serving)          │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI + Python 3.12)                    │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                       API Routes (REST)                          │   │
│  │  Auth │ Files │ Scans │ AI │ Dashboard │ Alerts │ Reports │ Users│   │
│  └───────┴───────┴───────┴────┴───────────┴────────┴─────────┴──────┘   │
│                           │                                              │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    Service Layer (Business Logic)                │   │
│  │  AuthService │ FileService │ ScanService │ AIService │ RiskSvc    │   │
│  │  AlertService│ ReportSvc  │ DashboardSvc │ GCSService │ DLPSvc    │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                           │                                              │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                 Repository Layer (Data Access)                   │   │
│  │       BaseRepository<T> │ UserRepo │ FileRepo │ ScanRepo         │   │
│  │       AlertRepo │ ReportRepo │ RiskRepo                           │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                           │                                              │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    Database (PostgreSQL 15+)                     │   │
│  │     users │ files │ scan_results │ risk_assessments │ alerts     │   │
│  │     reports │ compliance_log                                     │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└───────────────────────────┬──────────────────────────────────────────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
┌─────────────────┐ ┌──────────────┐ ┌──────────────────┐
│  Ollama (Llama3)│ │ Google Cloud │ │  SMTP / Email    │
│  AI Compliance  │ │  GCS / DLP   │ │  Alerting         │
│  Recommendations│ │  / Pub/Sub   │ │  Notifications    │
└─────────────────┘ └──────────────┘ └──────────────────┘
```

### Key Design Principles

- **Separation of Concerns**: Presentation, business logic, and data access are fully decoupled.
- **Dependency Injection**: Services and repositories are injected via FastAPI's `Depends()`.
- **Async-First**: The entire backend uses `asyncio` with `asyncpg` for non-blocking database operations.
- **Repository Pattern**: All data access goes through typed repositories that extend `BaseRepository<T>`.
- **Graceful Degradation**: External services (AI, GCS, DLP) degrade gracefully when unavailable.

---

## 2. Frontend Architecture

### Technology Stack

| Layer | Technology |
|---|---|
| Framework | React 18 |
| Build Tool | Vite 5 |
| Styling | TailwindCSS 3.4 + `tailwindcss-animate` |
| Routing | React Router DOM v6 |
| HTTP Client | Axios (with interceptors) |
| Charts | Recharts 2 + Chart.js 4 |
| Forms | React Hook Form |
| Animations | Framer Motion |
| Icons | Lucide React + React Icons |
| Notifications | React Hot Toast |
| State Mgmt | React Context + TanStack Query |

### Application Entry Point

```
main.jsx
  └── App.jsx
       ├── ThemeProvider (dark/light mode)
       └── AnimatedRoutes
            ├── /login          → Login page
            ├── /register       → Redirects to /login
            ├── / (ProtectedRoute → Layout)
            │    ├── /dashboard  → Dashboard (stats, charts, alerts, AI insights)
            │    ├── /upload     → File upload with drag-and-drop
            │    ├── /files      → File list with search/filter
            │    ├── /scans/:fileId → Scan results with risk assessment
            │    ├── /reports    → Report list
            │    ├── /reports/:id → Report detail and PDF download
            │    ├── /alerts     → Alert management
            │    └── /settings   → User settings and preferences
            └── * → Redirects to /dashboard
```

### Component Tree

```
src/
├── components/
│   ├── Layout/
│   │   ├── Layout.jsx          (Sidebar + Navbar + main content area)
│   │   ├── Navbar.jsx          (Top navigation with user menu)
│   │   └── Sidebar.jsx         (Navigation rail with route links)
│   ├── Auth/
│   │   ├── LoginForm.jsx       (Email/password login form)
│   │   └── RegisterForm.jsx    (Registration form)
│   ├── Dashboard/
│   │   ├── StatsCard.jsx       (KPI metric card)
│   │   ├── RiskChart.jsx       (Risk score bar/area chart)
│   │   ├── TrendChart.jsx      (Compliance trend line chart)
│   │   ├── FindingChart.jsx    (PII findings donut chart)
│   │   ├── ComplianceGauge.jsx (Radial compliance score gauge)
│   │   └── AlertWidget.jsx     (Recent alerts preview)
│   ├── Files/
│   │   ├── FileUpload.jsx      (Drag-and-drop upload zone)
│   │   └── FileList.jsx        (Paginated file table)
│   ├── Scans/
│   │   ├── ScanResults.jsx     (Findings table by data type)
│   │   ├── RiskScore.jsx       (Risk assessment display)
│   │   └── AIRecommendations.jsx (AI compliance suggestions)
│   ├── Alerts/
│   │   └── AlertList.jsx       (Alert listing with severity badges)
│   ├── Reports/
│   │   └── ReportList.jsx      (Report listing with download)
│   ├── Common/
│   │   ├── Loading.jsx         (Spinner/skeleton loader)
│   │   ├── EmptyState.jsx      (Empty data placeholder)
│   │   ├── ErrorState.jsx      (Error with retry)
│   │   ├── StatusBadge.jsx     (Severity/status badge)
│   │   └── ProtectedRoute.jsx  (Auth guard wrapper)
│   └── AI/
│       └── AIAssistant.jsx     (Chat interface for AI compliance Q&A)
├── context/
│   ├── AuthContext.jsx         (Authentication state management)
│   └── ThemeContext.jsx        (Dark/light mode toggling)
├── hooks/
│   └── useAuth.js              (Auth context consumer hook)
├── services/
│   ├── api.js                  (Axios instance with JWT interceptor)
│   ├── authService.js          (Login, register, google login, refresh)
│   ├── fileService.js          (Upload, list, delete, download files)
│   ├── scanService.js          (Start scan, get results, risk assessment)
│   ├── aiService.js            (Recommendations, summary, chat)
│   ├── dashboardService.js     (Stats, trends, distribution, compliance)
│   ├── alertService.js         (List alerts, mark read, stats)
│   └── reportService.js        (Generate, list, download reports)
├── utils/
│   └── constants.js            (Severity colors, risk levels, sidebar items)
└── pages/
    ├── Login.jsx               (Login page with Google OAuth)
    ├── Register.jsx            (Registration page)
    ├── Dashboard.jsx           (Full compliance dashboard)
    ├── Upload.jsx              (File upload page)
    ├── Files.jsx               (File management page)
    ├── ScanResults.jsx         (Scan findings page)
    ├── Reports.jsx             (Reports listing page)
    ├── ReportDetail.jsx        (Individual report view)
    ├── Alerts.jsx              (Alert management page)
    └── Settings.jsx            (User settings)
```

### API Client Architecture

The Axios client (`api.js`) implements automatic JWT token refresh:

```javascript
// Request interceptor: attach access token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Response interceptor: on 401, attempt refresh, retry original request
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401 && !originalRequest._retry) {
      // Call /auth/refresh with stored refresh_token
      // On success: update access_token, retry original request
      // On failure: clear tokens, redirect to /login
    }
  }
);
```

### Routing and Auth Guards

- `ProtectedRoute` wraps all authenticated pages and redirects to `/login` if unauthenticated.
- The `AuthContext` manages login, Google Sign-In, registration, and token storage.
- On app mount, `AuthContext` attempts to fetch the current user profile via `GET /auth/me` using the stored access token.

---

## 3. Backend Architecture

### Technology Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI 0.111 (Python 3.12) |
| ASGI Server | Uvicorn 0.30 |
| ORM | SQLAlchemy 2.0 (async) |
| DB Driver | asyncpg 0.29 |
| Validation | Pydantic v2 + pydantic-settings |
| Auth | python-jose (JWT) + bcrypt |
| PDF | ReportLab 4.2 |
| HTTP Client | httpx 0.27 |
| AI | Ollama HTTP API |
| Cloud SDK | google-cloud-storage, google-cloud-dlp |
| Testing | pytest + pytest-asyncio + pytest-cov |

### Project Structure

```
backend/
├── app/
│   ├── main.py                 # Application entry point
│   ├── server.py               # FastAPI app factory (create_app)
│   ├── api/
│   │   └── v1/
│   │       ├── auth/routes.py      # Authentication endpoints
│   │       ├── files/routes.py     # File management endpoints
│   │       ├── scans/routes.py     # Scan and risk endpoints
│   │       ├── ai/routes.py        # AI compliance endpoints
│   │       ├── alerts/routes.py    # Alert management endpoints
│   │       ├── reports/routes.py   # Report generation endpoints
│   │       ├── dashboard/routes.py # Dashboard data endpoints
│   │       ├── users/routes.py     # User management endpoints
│   │       └── health/routes.py    # Health check endpoint
│   ├── core/
│   │   ├── config/settings.py  # Pydantic settings (env vars)
│   │   ├── database/__init__.py # Async SQLAlchemy engine + session
│   │   └── security/__init__.py # JWT create/decode, password hashing, RBAC
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── user.py
│   │   ├── file.py
│   │   ├── scan.py
│   │   ├── alert.py
│   │   ├── report.py
│   │   └── compliance_log.py
│   ├── schemas/                # Pydantic request/response models
│   │   ├── auth.py
│   │   ├── file.py
│   │   ├── scan.py
│   │   ├── ai.py
│   │   ├── alert.py
│   │   ├── report.py
│   │   ├── dashboard.py
│   │   └── common.py
│   ├── services/               # Business logic layer
│   │   ├── auth/auth_service.py
│   │   ├── file/file_service.py
│   │   ├── detection/
│   │   │   ├── detection_engine.py  # Regex-based PII detection
│   │   │   └── scan_service.py      # Scan orchestration
│   │   ├── risk/risk_service.py     # Risk scoring
│   │   ├── ai/ai_service.py         # Ollama integration
│   │   ├── alerting/alert_service.py
│   │   ├── reporting/report_service.py
│   │   ├── dashboard/dashboard_service.py
│   │   ├── gcs/gcs_service.py       # Google Cloud Storage
│   │   └── dlp/dlp_service.py       # Google Cloud DLP
│   ├── repositories/           # Data access layer
│   │   ├── base.py             # Generic CRUD: BaseRepository<T>
│   │   ├── user_repository.py
│   │   ├── file_repository.py
│   │   ├── scan_repository.py
│   │   ├── risk_repository.py
│   │   ├── alert_repository.py
│   │   └── report_repository.py
│   ├── utils/
│   │   ├── exceptions.py       # Custom exception classes
│   │   └── logging.py          # Logging configuration
│   └── tests/                  # Test suite
│       ├── conftest.py
│       ├── api/
│       │   ├── test_auth_api.py
│       │   └── test_health_api.py
│       └── services/
│           ├── test_auth_service.py
│           ├── test_detection_engine.py
│           └── test_file_service.py
├── alembic/                    # Database migration scripts
├── alembic.ini
├── requirements.txt
└── Dockerfile
```

### Application Factory Pattern

The `server.py` file uses a factory function `create_app()` that:

1. Creates the FastAPI instance with title, version, and lifespan
2. Configures CORS middleware from settings
3. Registers custom exception handlers
4. Imports and registers all API routers under `/api/v1`
5. Handles startup/shutdown lifecycle (database init, connection pool)

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database, validate Google OAuth config
    await initialize_database()
    yield
    # Shutdown: close database connections
    await close_database_connection()
```

### Service Layer Pattern

Every service class follows dependency injection:

```python
class AuthService:
    def __init__(self, user_repository: UserRepository):
        self.user_repo = user_repository

    async def register_user(self, name, email, password) -> TokenResponse:
        # Business logic...
```

Services coordinate multiple repositories and external services. For example, `ScanService` orchestrates:

```
ScanService.start_scan(file_id, file_path, file_type)
  ├── DetectionEngine.detect_file(file_path, file_type)  → regex patterns
  ├── ScanResultRepository.create(...)  for each finding
  └── RiskService.assess_file(file_id)  → calculate risk score
```

### Repository Pattern

The generic `BaseRepository<T>` provides:

```python
class BaseRepository(Generic[ModelType]):
    async def create(self, **kwargs) -> ModelType
    async def get(self, id: str) -> Optional[ModelType]
    async def get_or_raise(self, id: str) -> ModelType
    async def get_all(self, skip, limit, order_by, **filters) -> tuple[list, int]
    async def update(self, id: str, **kwargs) -> ModelType
    async def delete(self, id: str) -> bool
    async def count(self, **filters) -> int
    async def exists(self, **filters) -> bool
```

Module-specific repositories extend the base with domain-specific queries:

```python
class ScanResultRepository(BaseRepository[ScanResult]):
    async def get_by_file_id(self, file_id, skip, limit) -> tuple[list, int]
    async def get_findings_summary(self, file_id) -> list[dict]
    async def get_all_findings_summary(self) -> list[dict]
    async def get_high_severity_findings(self, ...) -> list[ScanResult]
    async def delete_by_file_id(self, file_id) -> int
```

### Request Lifecycle

```
HTTP Request
  │
  ▼
CORS Middleware
  │
  ▼
FastAPI Router (path matched + parameters extracted)
  │
  ▼
Dependencies resolved (get_db → async session, get_current_user → JWT payload)
  │
  ▼
Route handler called → constructs service(s) → calls business logic
  │
  ▼
Service method → repository method(s) → database queries
  │
  ▼
Response serialized via Pydantic response_model → JSON returned
```

---

## 4. Database Schema and Relationships

### Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                              users                                  │
├─────────────────────────────────────────────────────────────────────┤
│ id (UUID PK) │ name │ email (UNIQUE) │ password_hash │ provider     │
│ google_id (UNIQUE) │ role │ is_active │ last_login │ created_at     │
│ updated_at │ profile_picture │ email_verified                       │
└───────────────────────┬─────────────────────────────────────────────┘
          │ 1                        │ 1
          │                          │
          ▼                          ▼
┌──────────────────┐   ┌──────────────────────────────┐
│     files        │   │         alerts               │
├──────────────────┤   ├──────────────────────────────┤
│ id (UUID PK)     │   │ id (UUID PK)                 │
│ user_id (FK) ────┤   │ file_id (FK nullable) ───────┤
│ original_name    │   │ user_id (FK nullable) ────┘  │
│ stored_name      │   │ alert_type │ severity         │
│ file_type        │   │ message │ is_read             │
│ file_size        │   │ created_at                    │
│ storage_path     │   └──────────────────────────────┘
│ gcs_path         │
│ scan_status      │         1
│ uploaded_at      │         │
│ updated_at       │         ▼
└───────┬──────────┘   ┌──────────────────────────────┐
        │ 1            │        reports                │
        │              ├──────────────────────────────┤
        ▼              │ id (UUID PK)                 │
┌──────────────────┐   │ user_id (FK nullable) ───────┤
│  scan_results    │   │ file_id (FK nullable)        │
├──────────────────┤   │ title │ report_type           │
│ id (UUID PK)     │   │ report_data (JSON)           │
│ file_id (FK) ────┤   │ pdf_path │ ai_summary         │
│ data_type        │   │ generated_at                 │
│ count │ severity │   └──────────────────────────────┘
│ sample_values    │
│ (JSON nullable)  │        1
│ context │ created│        │
└───────┬──────────┘        ▼
        │ 1          ┌──────────────────────────────┐
        │            │     risk_assessments         │
        ▼            ├──────────────────────────────┤
┌──────────────────┐ │ id (UUID PK)                 │
│ compliance_log   │ │ file_id (FK) ────────────────┤
├──────────────────┤ │ overall_score │ risk_level    │
│ id (UUID PK)     │ │ breakdown (JSON)             │
│ user_id (FK) ────┤ │ explanation │ created_at     │
│ action           │ └──────────────────────────────┘
│ resource_type    │
│ resource_id      │
│ details (JSON)   │
│ ip_address       │
│ created_at       │
└──────────────────┘
```

### Tables

#### `users`
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK, default uuid4 | Unique user identifier |
| name | VARCHAR(255) | NOT NULL | Display name |
| email | VARCHAR(255) | UNIQUE, NOT NULL, INDEX | Email address |
| password_hash | VARCHAR(255) | NULLABLE | bcrypt hash (null for Google-only) |
| provider | VARCHAR(20) | NOT NULL, DEFAULT 'LOCAL' | 'LOCAL' or 'GOOGLE' |
| google_id | VARCHAR(255) | UNIQUE, NULLABLE, INDEX | Google account ID |
| profile_picture | VARCHAR(1024) | NULLABLE | Google profile photo URL |
| email_verified | BOOLEAN | DEFAULT false | Google email verification |
| role | VARCHAR(50) | DEFAULT 'user', INDEX | admin, analyst, user, viewer |
| is_active | BOOLEAN | DEFAULT true | Soft-delete flag |
| last_login | TIMESTAMPTZ | NULLABLE | Last successful login |
| created_at | TIMESTAMPTZ | NOT NULL | Account creation timestamp |
| updated_at | TIMESTAMPTZ | NOT NULL | Last update timestamp |

#### `files`
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK, default uuid4 | Unique file identifier |
| user_id | UUID | FK → users.id ON DELETE CASCADE, INDEX | Owner |
| original_name | VARCHAR(255) | NOT NULL | Original filename |
| stored_name | VARCHAR(255) | NOT NULL | UUID-based storage name |
| file_type | VARCHAR(50) | NOT NULL, INDEX | csv, xlsx, pdf, txt |
| file_size | BIGINT | DEFAULT 0 | Size in bytes |
| storage_path | VARCHAR(500) | NOT NULL | Local filesystem path |
| gcs_path | VARCHAR(500) | NULLABLE | Google Cloud Storage path |
| scan_status | VARCHAR(50) | DEFAULT 'pending', INDEX | pending, scanning, completed, failed |
| uploaded_at | TIMESTAMPTZ | NOT NULL | Upload timestamp |
| updated_at | TIMESTAMPTZ | NOT NULL | Last update |

#### `scan_results`
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK, default uuid4 | Unique result identifier |
| file_id | UUID | FK → files.id ON DELETE CASCADE, INDEX | Scanned file |
| data_type | VARCHAR(100) | NOT NULL, INDEX | Aadhaar, PAN, Email, Phone, CreditCard |
| count | INTEGER | DEFAULT 0 | Number of occurrences |
| severity | VARCHAR(50) | NOT NULL, INDEX | CRITICAL, HIGH, MEDIUM, LOW |
| sample_values | JSON | NULLABLE | Up to 5 sample matches |
| context | TEXT | NULLABLE | Surrounding context |
| created_at | TIMESTAMPTZ | NOT NULL | Detection timestamp |

#### `risk_assessments`
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK, default uuid4 | Unique assessment identifier |
| file_id | UUID | FK → files.id ON DELETE CASCADE, INDEX | Assessed file |
| overall_score | FLOAT | NOT NULL | Numerical risk score |
| risk_level | VARCHAR(50) | NOT NULL | LOW (0-30), MEDIUM (31-70), HIGH (71+) |
| breakdown | JSON | NULLABLE | Per-data-type contribution |
| explanation | TEXT | NULLABLE | Human-readable analysis |
| created_at | TIMESTAMPTZ | NOT NULL | Assessment timestamp |

#### `alerts`
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK, default uuid4 | Unique alert identifier |
| file_id | UUID | FK → files.id ON DELETE SET NULL, INDEX | Related file (nullable) |
| user_id | UUID | FK → users.id ON DELETE SET NULL, INDEX | Alert recipient |
| alert_type | VARCHAR(100) | NOT NULL, INDEX | high_risk, excessive_findings |
| severity | VARCHAR(50) | NOT NULL, INDEX | CRITICAL, HIGH, MEDIUM, LOW |
| message | TEXT | NULLABLE | Human-readable alert |
| is_read | BOOLEAN | DEFAULT false | Read status |
| created_at | TIMESTAMPTZ | NOT NULL | Creation timestamp |

#### `reports`
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK, default uuid4 | Unique report identifier |
| user_id | UUID | FK → users.id ON DELETE SET NULL, INDEX | Report owner |
| file_id | UUID | FK → files.id ON DELETE SET NULL | Related file |
| title | VARCHAR(255) | NOT NULL | Report title |
| report_type | VARCHAR(50) | NOT NULL, INDEX | compliance, audit, summary |
| report_data | JSON | NULLABLE | Structured report content |
| pdf_path | VARCHAR(500) | NULLABLE | Filesystem path to PDF |
| ai_summary | TEXT | NULLABLE | AI-generated summary |
| generated_at | TIMESTAMPTZ | NOT NULL | Generation timestamp |

#### `compliance_log`
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK, default uuid4 | Unique log entry |
| user_id | UUID | FK → users.id ON DELETE SET NULL, INDEX | Acting user |
| action | VARCHAR(100) | NOT NULL, INDEX | Performed action |
| resource_type | VARCHAR(100) | NULLABLE | File, scan, report, etc. |
| resource_id | VARCHAR(255) | NULLABLE | UUID of resource |
| details | JSON | NULLABLE | Action context/metadata |
| ip_address | VARCHAR(50) | NULLABLE | Request origin IP |
| created_at | TIMESTAMPTZ | NOT NULL | Action timestamp |

### Indexes

| Table | Index | Column(s) | Type |
|---|---|---|---|
| users | ix_users_email | email | UNIQUE |
| users | ix_users_google_id | google_id | UNIQUE |
| users | ix_users_role | role | Standard |
| files | ix_files_user_id | user_id | Standard |
| files | ix_files_file_type | file_type | Standard |
| files | ix_files_scan_status | scan_status | Standard |
| scan_results | ix_scan_results_file_id | file_id | Standard |
| scan_results | ix_scan_results_data_type | data_type | Standard |
| scan_results | ix_scan_results_severity | severity | Standard |
| risk_assessments | ix_risk_assessments_file_id | file_id | Standard |
| alerts | ix_alerts_file_id | file_id | Standard |
| alerts | ix_alerts_user_id | user_id | Standard |
| alerts | ix_alerts_alert_type | alert_type | Standard |
| alerts | ix_alerts_severity | severity | Standard |
| reports | ix_reports_user_id | user_id | Standard |
| reports | ix_reports_report_type | report_type | Standard |
| compliance_log | ix_compliance_log_user_id | user_id | Standard |
| compliance_log | ix_compliance_log_action | action | Standard |

---

## 5. Authentication Flow

### JWT Token Authentication

```
┌──────────┐          ┌──────────┐          ┌──────────┐
│  Client  │          │  Server  │          │ Database │
└────┬─────┘          └────┬─────┘          └────┬─────┘
     │                     │                     │
     │  POST /auth/login   │                     │
     │  {email, password}  │                     │
     │────────────────────>│                     │
     │                     │  Get user by email   │
     │                     │────────────────────>│
     │                     │<────────────────────│
     │                     │                     │
     │                     │  Verify bcrypt hash  │
     │                     │                     │
     │                     │  Create JWT tokens:  │
     │                     │  - access_token      │
     │                     │    (15 min, HS256)   │
     │                     │  - refresh_token     │
     │                     │    (7 days, HS256)   │
     │                     │                     │
     │  200 {access_token, │                     │
     │  refresh_token,     │                     │
     │  token_type, user}  │                     │
     │<────────────────────│                     │
     │                     │                     │
     │  ─── Subsequent requests ───              │
     │                     │                     │
     │  GET /files         │                     │
     │  Authorization:     │                     │
     │  Bearer <access>    │                     │
     │────────────────────>│                     │
     │                     │  Decode + validate  │
     │                     │  JWT (verify sig,   │
     │                     │  check exp, type)   │
     │                     │                     │
     │<────────────────────│                     │
     │  200 OK             │                     │
     │                     │                     │
     │  ─── Token refresh ───                   │
     │                     │                     │
     │  POST /auth/refresh │                     │
     │  {refresh_token}    │                     │
     │────────────────────>│                     │
     │                     │  Decode refresh JWT │
     │                     │  Verify type=refresh│
     │                     │  Issue new tokens   │
     │<────────────────────│                     │
     │  200 {new access,   │                     │
     │  new refresh, user} │                     │
```

### Key Implementation Details

- **Access Token**: Short-lived (15 minutes default), contains `sub` (user ID), `role`, `type: "access"`, `exp`, `iat`.
- **Refresh Token**: Long-lived (7 days), contains same fields with `type: "refresh"`.
- **Password Hashing**: bcrypt with 12 rounds via `passlib`.
- **Frontend Token Storage**: Tokens stored in `localStorage`.
- **Frontend Auto-Refresh**: Axios interceptor catches 401, calls `/auth/refresh`, retries the original request.

### Google OAuth 2.0 Flow

```
1. User clicks "Continue with Google"
2. Google Identity Services (GIS) shows account picker
3. Google returns a credential (ID token JWT)
4. Frontend sends credential to POST /api/v1/auth/google-login
5. Server verifies the ID token:
   a. Fetches Google's public keys from https://www.googleapis.com/oauth2/v3/certs
   b. Verifies JWT signature, audience (GOOGLE_CLIENT_ID), issuer, expiration
   c. Falls back to PyJWT if google-auth library is unavailable
6. Server looks up or creates user by google_id or email
7. Returns JWT token pair (same as local auth)
```

### Role-Based Access Control (RBAC)

```python
ROLE_HIERARCHY = {"admin": 4, "analyst": 3, "user": 2, "viewer": 1}
```

- `admin`: Full system access, user management, all files/scans
- `analyst`: Can view all scans and generate reports
- `user`: Can upload own files, scan own files, view own data
- `viewer`: Read-only access to dashboards and reports

---

## 6. PII Detection Pipeline

### Pipeline Flow

```
File Upload
  │
  ▼
FileService.upload_file()
  ├── Validate extension (.csv, .xlsx, .pdf, .txt)
  ├── Validate file size (max 50MB)
  ├── Validate magic bytes (PDF: %PDF, XLSX: PK\x03\x04)
  ├── Write to disk (UUID-based filename)
  └── Create database record (scan_status = "pending")
  │
  ▼
POST /api/v1/scans/start/{file_id}
  │
  ▼
ScanService.start_scan()
  │
  ├── DetectionEngine.detect_file(path, type)
  │    │
  │    ├── Parse file based on type:
  │    │   ├── .csv  → csv.reader
  │    │   ├── .xlsx → openpyxl (read-only mode)
  │    │   ├── .pdf  → PyPDF2.PdfReader
  │    │   └── .txt  → utf-8 read
  │    │
  │    ├── Run regex patterns:
  │    │   ├── Aadhaar    → \b[2-9]\d{11}\b
  │    │   ├── PAN        → [A-Z]{5}[0-9]{4}[A-Z]{1}
  │    │   ├── Email      → [a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}
  │    │   ├── Phone      → (?:\+91|0)?[6-9]\d{9}
  │    │   └── CreditCard → \b(?:\d[ -]*?){13,16}\b → Luhn check
  │    │
  │    └── Return structured findings:
  │        [{data_type, count, sample_values, severity}, ...]
  │
  ├── Persist findings to scan_results table
  │
  ├── RiskService.assess_file(file_id)
  │    ├── Fetch all ScanResults for file
  │    ├── Calculate weighted score:
  │    │   Aadhaar=50, PAN=40, CreditCard=60,
  │    │   Email=10, Phone=10 (per occurrence × weight)
  │    ├── Classify risk level:
  │    │   LOW (0-30), MEDIUM (31-70), HIGH (71+)
  │    └── Persist to risk_assessments table
  │
  └── AlertService.check_and_alert(file_id)
       ├── If risk_score >= 71 → create HIGH alert
       └── If total_findings >= 100 → create MEDIUM alert
  │
  ▼
Update file.scan_status = "completed"
```

### PII Detection Patterns

| Data Type | Regex Pattern | Severity | Validation |
|---|---|---|---|
| Aadhaar | `\b[2-9]\d{11}\b` | CRITICAL | Must start with 2-9, 12 digits |
| PAN | `[A-Z]{5}[0-9]{4}[A-Z]{1}` | HIGH | 5 letters + 4 digits + 1 letter |
| Email | Full RFC-compatible pattern | LOW | Standard email format |
| Phone (India) | `(?:\+91\|0)?[6-9]\d{9}` | MEDIUM | 10 digits starting with 6-9, optional +91/0 prefix |
| Credit Card | `\b(?:\d[ -]*?){13,16}\b` | CRITICAL | Luhn algorithm validation |

### Optional: Google Cloud DLP Integration

When `DLP_ENABLED=True`, the platform can also scan using Google Cloud Data Loss Prevention API:

```python
class DLPService:
    INFO_TYPES = [
        "US_SOCIAL_SECURITY_NUMBER", "EMAIL_ADDRESS", "PHONE_NUMBER",
        "CREDIT_CARD_NUMBER", "INDIA_AADHAAR", "INDIA_PAN",
        "PERSON_NAME", "US_BANK_NUMBER", "DATE_OF_BIRTH",
    ]
```

DLP findings are mapped to the same internal format as regex findings. The regex engine always runs first; DLP serves as an optional enhancement.

---

## 7. AI Integration

### Architecture

```
AI Service (AIService)
  │
  ├── generate_recommendations(file_id, scan_results, risk)
  │    └── POST /api/generate to Ollama with recommendation prompt
  │
  ├── generate_summary(file_id, scan_results, risk)
  │    └── POST /api/generate to Ollama with summary prompt
  │
  ├── generate_executive_report(scan_results, risk)
  │    └── POST /api/generate to Ollama with executive prompt
  │
  └── chat(message, conversation_history)
       └── POST /api/generate to Ollama with chat prompt
```

### Prompt Templates

The AI service uses structured prompts designed for privacy compliance expertise:

**Recommendation Prompt**: Asks the model to analyze findings and return JSON with risk summary, compliance impact, recommended actions, executive summary, and detailed per-finding recommendations.

**Summary Prompt**: Condenses findings into a JSON response with summary, key findings list, risk level, and suggested actions.

**Executive Report Prompt**: Generates a comprehensive prose report covering executive summary, key risk areas, compliance posture, remediations, and strategic roadmap.

**Chat Prompt**: Provides conversational AI assistant capabilities with context from the last 10 messages, confined to privacy/security/compliance topics.

### Fallback Behavior

When AI is disabled or Ollama is unreachable:

```python
# Default recommendations
{
    "risk_summary": "AI service unavailable. Enable Ollama with Llama 3 for AI-powered recommendations.",
    "compliance_impact": "Unable to assess compliance impact without AI service.",
    "recommended_actions": [
        "Review findings manually through the dashboard",
        "Enable AI service in platform settings",
        "Ensure Ollama is running with Llama 3 model",
    ],
    "executive_summary": "AI compliance analysis unavailable. Please configure the AI service.",
    "detailed_recommendations": [],
}
```

---

## 8. Security Architecture

### Authentication

- **Password Storage**: bcrypt with 12 salt rounds (`passlib.hash.bcrypt`)
- **JWT Signing**: HMAC-SHA256 (`HS256`) with configurable `SECRET_KEY`
- **Token Expiry**: Access tokens 15 minutes, refresh tokens 7 days
- **Token Types**: Access and refresh tokens are distinct (verified by `type` claim)

### Authorization

- Role hierarchy: admin (4) > analyst (3) > user (2) > viewer (1)
- File ownership enforced at the route level via `_verify_file_ownership`
- Admin role required for user management and cross-user operations

### Input Validation

- All request/response models use Pydantic v2 validators
- Password strength enforced: minimum 8 chars, must contain uppercase, lowercase, and digit
- Email validated via `pydantic.EmailStr`
- File uploads: extension whitelist, size limit, magic byte verification

### CORS

```python
CORS_ORIGINS = "http://localhost:5173,http://localhost:3000"
# Parsed into list and set on CORSMiddleware
```

### File Upload Security

- Allowed extensions: `.csv`, `.xlsx`, `.pdf`, `.txt`
- Maximum file size: 50MB (configurable)
- Magic byte validation for `.pdf` (%PDF) and `.xlsx` (PK\x03\x04)
- Files stored with UUID-based names (no path traversal)
- Storage directory outside web root

### HTTP Security Headers

Applied via Nginx reverse proxy in production:

- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Strict-Transport-Security (when HTTPS is configured)

---

## 9. Deployment Architecture

### Docker Deployment (Recommended)

```
┌─────────────────────────────────────────────────────────────┐
│                   Docker Compose Network                     │
│                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │  Nginx   │───▶│ Frontend │    │  Ollama  │              │
│  │  :80     │    │  :3000   │    │  :11434  │              │
│  └────┬─────┘    └──────────┘    └──────────┘              │
│       │                                                     │
│       │           ┌──────────┐    ┌──────────┐              │
│       └──────────▶│ Backend  │───▶│PostgreSQL│              │
│                   │  :8000   │    │  :5432   │              │
│                   └──────────┘    └──────────┘              │
│                                                              │
│  Volumes: postgres_data, ollama_data                         │
│  Mounts: ./uploads, ./reports, ./logs, ./backend             │
└─────────────────────────────────────────────────────────────┘
```

### CI/CD Pipeline (GitHub Actions)

```
push to main
  │
  ├── test-backend (pytest, coverage)
  ├── test-frontend (lint, build check)
  │
  ├── build-and-push-backend (Docker Hub)
  ├── build-and-push-frontend (Docker Hub)
  │
  ├── deploy-backend-render (Render API)
  └── deploy-frontend-vercel (Vercel CLI)
```

### Hosting Strategy

| Component | Hosting | URL |
|---|---|---|
| Frontend | Vercel | `https://app.privacy-platform.com` |
| Backend API | Render | `https://api.privacy-platform.com` |
| Database | Supabase / Render PostgreSQL | Managed PostgreSQL 15+ |
| AI (Ollama) | Self-hosted / GPU instance | Internal network |
| File Storage | Local disk + GCS (optional) | Configurable |
| Logging/Monitoring | Prometheus + Grafana | Optional |

### Environment-Specific Configuration

| Setting | Development | Staging | Production |
|---|---|---|---|
| Database | SQLite or local PostgreSQL | PostgreSQL (Supabase) | PostgreSQL (Supabase HA) |
| AI | Local Ollama | Cloud Ollama | Production Ollama cluster |
| Storage | Local disk | GCS | GCS with replication |
| Debug | True | False | False |
| CORS | localhost:5173 | Staging URL | Production URL |
| Log Level | DEBUG | INFO | WARNING |
