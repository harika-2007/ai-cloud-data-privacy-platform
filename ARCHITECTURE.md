# AI-Powered Cloud Data Privacy Compliance & Security Monitoring Platform

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Client Layer                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │   React SPA      │  │   React Admin    │  │   API Clients    │  │
│  │   (Vercel)       │  │   (Vercel)       │  │   (Postman/curl) │  │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘  │
└───────────┼──────────────────────┼──────────────────────┼────────────┘
            │                      │                      │
            │         HTTPS/REST   │         JWT Auth     │
            ▼                      ▼                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        API Gateway Layer                              │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │           FastAPI Application (Render)                        │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────┐  │   │
│  │  │  Auth    │ │  Files   │ │  Scans   │ │  Dashboard     │  │   │
│  │  │  Module  │ │  Module  │ │  Module  │ │  Module        │  │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └────────────────┘  │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────┐  │   │
│  │  │  AI      │ │  Reports │ │  Alerts  │ │  Health/Config │  │   │
│  │  │  Module  │ │  Module  │ │  Module  │ │  Module        │  │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────┘   │
└───────────────────────┬─────────────────────────────────────────────┘
                        │
          ┌─────────────┼─────────────┬─────────────────┐
          ▼             ▼             ▼                 ▼
┌─────────────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐
│   PostgreSQL    │ │  Google  │ │  Google  │ │   Google Pub/Sub │
│   (Supabase)    │ │  Cloud   │ │  Cloud   │ │   (Async Events) │
│                 │ │  Storage │ │  DLP API │ │                  │
│  - users        │ │  (Files) │ │  (PII    │ │  - scan.events   │
│  - files        │ │          │ │   Detect)│ │  - alert.events  │
│  - scan_results │ │          │ │          │ │  - report.events │
│  - alerts       │ └──────────┘ └──────────┘ └──────────────────┘
│  - reports      │
└─────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────────┐
│                    AI Layer                                        │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │  Ollama (Local/Cloud)                                      │   │
│  │  - Llama 3 / Qwen Models                                  │   │
│  │  - Compliance Recommendations                             │   │
│  │  - Risk Summaries                                          │   │
│  │  - Executive Reports                                       │   │
│  └────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

## System Architecture Patterns

### Clean Architecture Layers

```
┌──────────────────────────────────────────────────────────────────┐
│                    Presentation Layer                              │
│  API Routes → Request/Response Models → Validation               │
├──────────────────────────────────────────────────────────────────┤
│                    Service Layer                                   │
│  Business Logic → Orchestration → Workflow                       │
├──────────────────────────────────────────────────────────────────┤
│                    Repository Layer                                │
│  Data Access → ORM Queries → Database Operations                 │
├──────────────────────────────────────────────────────────────────┤
│                    Domain Layer                                    │
│  Entities → Value Objects → Domain Events                        │
└──────────────────────────────────────────────────────────────────┘
```

### Repository-Service Pattern

```
┌──────────┐     ┌──────────┐     ┌──────────────┐     ┌──────────┐
│  Route   │────▶│ Service  │────▶│  Repository  │────▶│  DB      │
│  (API)   │     │(Business)│     │  (Data)      │     │(Postgres)│
└──────────┘     └──────────┘     └──────────────┘     └──────────┘
```

## Folder Structure

```
privacy-platform/
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── auth/          # Authentication endpoints
│   │   │   ├── users/         # User management
│   │   │   ├── files/         # File upload/management
│   │   │   ├── scans/         # Scan operations
│   │   │   ├── reports/       # Report generation
│   │   │   ├── alerts/        # Alert management
│   │   │   ├── dashboard/     # Analytics endpoints
│   │   │   ├── ai/           # AI recommendation endpoints
│   │   │   └── health/       # Health check
│   │   ├── core/
│   │   │   ├── config/       # Application configuration
│   │   │   ├── security/     # JWT, RBAC, passwords
│   │   │   └── database/     # DB connection, session
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   ├── repositories/     # Data access layer
│   │   ├── utils/            # Helpers, validators
│   │   └── tests/            # Test suite
│   ├── alembic/              # Database migrations
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/            # Page components
│   │   ├── services/         # API client services
│   │   ├── hooks/            # Custom hooks
│   │   ├── context/          # React contexts
│   │   └── utils/            # Helpers
│   ├── package.json
│   └── Dockerfile
├── infrastructure/
│   ├── docker/               # Docker compose files
│   └── github/               # GitHub Actions
├── cloud-functions/          # GCP Cloud Functions
└── docs/                     # Documentation
```

## Database Schema (ERD)

```sql
-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Files
CREATE TABLE files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    original_name VARCHAR(255) NOT NULL,
    stored_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size BIGINT DEFAULT 0,
    storage_path VARCHAR(500),
    gcs_path VARCHAR(500),
    scan_status VARCHAR(50) DEFAULT 'pending',
    uploaded_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Scan Results
CREATE TABLE scan_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID REFERENCES files(id),
    data_type VARCHAR(100) NOT NULL,
    count INTEGER DEFAULT 0,
    severity VARCHAR(50) NOT NULL,
    sample_values JSONB,
    context TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Risk Assessments
CREATE TABLE risk_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID REFERENCES files(id),
    overall_score FLOAT NOT NULL,
    risk_level VARCHAR(50) NOT NULL,
    breakdown JSONB,
    explanation TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Alerts
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID REFERENCES files(id),
    user_id UUID REFERENCES users(id),
    alert_type VARCHAR(100) NOT NULL,
    severity VARCHAR(50) NOT NULL,
    message TEXT,
    is_read BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Reports
CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    file_id UUID REFERENCES files(id),
    title VARCHAR(255) NOT NULL,
    report_type VARCHAR(50) NOT NULL,
    report_data JSONB,
    ai_summary TEXT,
    generated_at TIMESTAMP DEFAULT NOW()
);

-- Compliance Log
CREATE TABLE compliance_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id UUID,
    details JSONB,
    ip_address VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);
```

## API Endpoints Design

### Authentication
```
POST   /api/v1/auth/register          # Register new user
POST   /api/v1/auth/login             # Login, get tokens
POST   /api/v1/auth/refresh           # Refresh token
POST   /api/v1/auth/logout            # Logout
GET    /api/v1/auth/me                # Get current user
```

### File Management
```
POST   /api/v1/files/upload           # Upload file
GET    /api/v1/files                   # List files
GET    /api/v1/files/{id}             # Get file details
DELETE /api/v1/files/{id}             # Delete file
GET    /api/v1/files/{id}/download    # Download file
```

### Scanning
```
POST   /api/v1/scans/start/{file_id}  # Start scan
GET    /api/v1/scans/{id}             # Get scan result
GET    /api/v1/scans/file/{file_id}   # Get scans for file
GET    /api/v1/scans                   # List all scans
```

### Risk Assessment
```
GET    /api/v1/risk/file/{file_id}    # Get risk assessment
GET    /api/v1/risk/summary           # Get risk summary
```

### AI Compliance
```
POST   /api/v1/ai/recommend/{file_id} # Get AI recommendations
POST   /api/v1/ai/summary/{file_id}   # Get AI summary
POST   /api/v1/ai/executive-report     # Generate executive report
```

### Dashboard
```
GET    /api/v1/dashboard/stats        # Dashboard statistics
GET    /api/v1/dashboard/trends       # Risk trends
GET    /api/v1/dashboard/distribution # Risk distribution
GET    /api/v1/dashboard/compliance   # Compliance score
```

### Alerts
```
GET    /api/v1/alerts                  # List alerts
PUT    /api/v1/alerts/{id}/read       # Mark as read
GET    /api/v1/alerts/stats           # Alert statistics
```

### Reports
```
POST   /api/v1/reports/generate       # Generate report
GET    /api/v1/reports                 # List reports
GET    /api/v1/reports/{id}           # Get report
GET    /api/v1/reports/{id}/download  # Download PDF
```

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Frontend | React 18, Vite, TailwindCSS, Chart.js |
| Backend | Python 3.12+, FastAPI, SQLAlchemy 2.0 |
| Database | PostgreSQL 15+ (Supabase) |
| Auth | JWT (access + refresh tokens), bcrypt |
| AI Integration | Ollama (Llama 3 / Qwen) |
| Cloud Storage | Google Cloud Storage |
| PII Detection | Google Cloud DLP API + Regex Engine |
| Async Events | Google Pub/Sub |
| Container | Docker, Docker Compose |
| CI/CD | GitHub Actions |
| Deployment | Vercel (FE), Render (BE), Supabase (DB) |

## Security Architecture

### Authentication Flow
```
User → Login → JWT Access Token (15min) + Refresh Token (7d)
     → Protected Routes → Verify Token → RBAC Check → Resource Access
```

### RBAC Roles
- `admin`: Full system access
- `analyst`: View scans, generate reports
- `user`: Upload files, view own scans
- `viewer`: Read-only dashboard access

## Data Flow

### File Upload and Scan Pipeline
```
Upload → Validate → Store (GCS + DB) → Queue Scan →
  Regex Detection → Cloud DLP → Risk Scoring →
  AI Analysis → Generate Alerts → Update Dashboard
```

## Error Handling Strategy
- All exceptions caught at service layer
- Standardized error response format
- HTTP status codes: 200, 201, 400, 401, 403, 404, 409, 422, 500
- Validation errors via Pydantic
- Graceful fallbacks for cloud service failures
