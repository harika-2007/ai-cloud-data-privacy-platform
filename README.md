# AI-Powered Cloud Data Privacy Compliance & Security Monitoring Platform

A cloud-native platform for detecting sensitive data (Aadhaar, PAN, Email, Phone, Credit Cards), assessing privacy risks, providing AI-generated compliance recommendations, generating reports, and monitoring compliance through a centralized dashboard.

---

## Overview

This platform enables organizations to:

- **Upload** files (CSV, XLSX, PDF, TXT) containing potential PII
- **Detect** sensitive data patterns using regex-based detection and optional Google Cloud DLP integration
- **Score** privacy risk automatically with configurable severity thresholds
- **Analyze** findings through AI-powered compliance recommendations (Ollama / Llama 3)
- **Alert** on high-risk findings with severity-based notifications
- **Report** with auto-generated PDF compliance and audit reports
- **Monitor** via a real-time dashboard with trends, distribution charts, and compliance metrics

---

## Features

- **PII Detection Engine** -- Regex-based detection for Aadhaar, PAN, Email, Phone, Credit Card, SSN, Passport, and more
- **AI Compliance Recommendations** -- Ollama integration provides contextual remediation advice and executive summaries
- **Risk Scoring** -- Multi-factor risk calculation with configurable thresholds
- **Interactive Dashboard** -- Real-time charts, trend analysis, compliance scoring, and risk distribution
- **Automated Alerts** -- Severity-based alerting with read/unread tracking
- **PDF Report Generation** -- Auto-generated compliance and audit reports with download support
- **Cloud DLP Integration** -- Optional Google Cloud Data Loss Prevention API for enhanced detection
- **Google Cloud Storage** -- Optional GCS integration for scalable file storage
- **Event-Driven Architecture** -- Pub/Sub topics for scan, alert, and report events
- **Role-Based Access Control** -- Admin, Analyst, User, and Viewer roles with hierarchy-based permissions
- **Google OAuth 2.0** -- Google Sign-In as the primary authentication method with auto-provisioning
- **JWT Authentication** -- Access and refresh token-based auth with bcrypt password hashing

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18, Vite, TailwindCSS, Chart.js, Recharts, React Router |
| **Backend** | Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Pydantic v2 |
| **Database** | PostgreSQL 15+ with asyncpg driver |
| **Authentication** | Google OAuth 2.0 (primary), JWT (access + refresh tokens), bcrypt password hashing |
| **AI / ML** | Ollama (Llama 3 / Qwen) for compliance recommendations |
| **Cloud** | Google Cloud Storage, Cloud DLP, Pub/Sub |
| **Containerization** | Docker & Docker Compose |
| **CI/CD** | GitHub Actions, Docker Hub |
| **Deployment** | Render (backend), Vercel (frontend) |
| **Infrastructure** | Terraform (GCP resources) |

---

## Architecture

```
                         +---------------------+
                         |    React Frontend    |
                         |  (Vercel / Docker)   |
                         +----------+----------+
                                    |
                              HTTP/API
                                    |
                    +---------------+---------------+
                    |                               |
            +-------v--------+            +---------v--------+
            |  FastAPI Backend |            |  Ollama Server   |
            |  (Render / Docker)|            |  (Llama 3 / AI) |
            +--------+--------+            +---------+--------+
                     |                               |
          +----------v----------+                    |
          |   PostgreSQL 15     |                    |
          |  (Supabase / Docker)|                    |
          +----------+----------+                    |
                     |                               |
          +----------v----------+                    |
          |   Google Cloud      |                    |
          |  - Storage (files)  |                    |
          |  - DLP (detection)  |                    |
          |  - Pub/Sub (events) |                    |
          +---------------------+                    |

     CI/CD Pipeline:
       GitHub Actions --> Docker Hub --> Render / Vercel

     Infrastructure (Terraform):
       GCS Bucket --> DLP API --> Pub/Sub Topics --> IAM Roles
```

### Data Flow

1. User authenticates via Google Sign-In (primary) or email/password (legacy)
2. File uploaded through the API is stored locally or in GCS
3. Scan is initiated: detection engine scans for PII patterns
4. Risk assessment calculated based on findings and configurable thresholds
5. AI compliance recommendations generated via Ollama
6. Alerts created for high-risk findings
7. Reports generated with PDF output
8. Dashboard aggregates all data for visualization

---

## Project Structure

```
privacy-platform/
├── backend/
│   ├── app/
│   │   ├── api/v1/            # API routes (auth, files, scans, reports, alerts, dashboard, ai, health, users)
│   │   ├── core/              # Config, database, security
│   │   ├── models/            # SQLAlchemy ORM models
│   │   ├── schemas/           # Pydantic v2 schemas
│   │   ├── services/          # Business logic services
│   │   ├── repositories/      # Data access layer
│   │   ├── utils/             # Exceptions, logging
│   │   └── tests/             # Test suite
│   ├── alembic/               # Database migrations
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── pages/             # Page components
│   │   ├── services/          # API client services
│   │   ├── hooks/             # Custom React hooks
│   │   ├── context/           # Auth context provider
│   │   └── utils/             # Constants and helpers
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
├── infrastructure/
│   ├── docker/docker-compose.yml    # Local dev orchestration
│   ├── github/workflows/            # CI/CD pipelines
│   └── terraform/                   # GCP infrastructure as code
├── cloud-functions/
│   └── scan_trigger/               # GCP Cloud Function
├── scripts/
│   ├── setup.sh                    # Automated setup script
│   └── seed.py                     # Database seeding
├── docs/
│   ├── api.md                      # API documentation
│   └── setup.md                    # Setup guide
├── render.yaml                     # Render Blueprint config
├── vercel.json                     # Vercel deployment config
└── .gitignore
```

---

## Prerequisites

- Python 3.12+
- Node.js 18+
- PostgreSQL 15+
- Docker & Docker Compose (for containerized setup)
- Ollama (for AI compliance features -- optional)
- A Google Cloud Platform account (for DLP/GCS -- optional)

---

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/privacy-platform.git
cd privacy-platform
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate (Linux/macOS)
source .venv/bin/activate

# Activate (Windows)
# .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
# Edit .env with your database credentials and secret key

# Run database migrations
alembic upgrade head

# Seed demo data
python ../scripts/seed.py

# Start the API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Configure Google OAuth 2.0

1. Go to the [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create a new project or select an existing one
3. Navigate to **APIs & Services → Credentials**
4. Click **Create Credentials → OAuth 2.0 Client ID**
5. Select **Web application** as the application type
6. Add **Authorized JavaScript origins**:
   - `http://localhost:5173`
   - `http://localhost:5174`
7. Add **Authorized redirect URIs**:
   - `http://localhost:8000/api/v1/auth/google/callback`
8. Copy the generated **Client ID** and **Client Secret**

Set the variables in your environment:

```bash
# backend/.env
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback
```

### 4. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### 4. Access the Application

| Resource | URL |
|----------|-----|
| Frontend | http://localhost:5173 |
| API Docs | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Health Check | http://localhost:8000/api/v1/health |

### 5. Docker Setup (Alternative)

```bash
# Start all services
cd infrastructure/docker
docker-compose up -d

# Pull the AI model (first time only)
docker exec -it privacy-ollama ollama pull llama3

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### Default Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@example.com | Admin@123 |
| Analyst | analyst@example.com | Analyst@123 |
| User | user1@example.com | User@12345 |

---

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SECRET_KEY` | JWT signing key (min 32 chars) | `change-me-in-production` | Yes |
| `DATABASE_URL` | PostgreSQL async connection string | `postgresql+asyncpg://...` | Yes |
| `DATABASE_SYNC_URL` | PostgreSQL sync connection string | `postgresql://...` | Yes |
| `ENVIRONMENT` | Runtime environment | `development` | Yes |
| `DEBUG` | Enable debug mode | `True` | No |
| `LOG_LEVEL` | Logging verbosity | `INFO` | No |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:5173,...` | Yes |
| `OLLAMA_BASE_URL` | Ollama API endpoint | `http://localhost:11434` | If AI enabled |
| `OLLAMA_MODEL` | Ollama model name | `llama3` | No |
| `AI_ENABLED` | Enable AI recommendations | `True` | No |
| `GOOGLE_CLIENT_ID` | Google OAuth 2.0 Client ID | `` | For Google Sign-In |
| `GOOGLE_CLIENT_SECRET` | Google OAuth 2.0 Client Secret | `` | For Google Sign-In |
| `GOOGLE_REDIRECT_URI` | Google OAuth redirect URI | `http://localhost:8000/api/v1/auth/google/callback` | For Google Sign-In |
| `MAX_UPLOAD_SIZE_MB` | Max file upload size (MB) | `50` | No |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID | `` | For GCS/DLP |
| `GCS_BUCKET_NAME` | GCS bucket name | `privacy-platform-uploads` | For GCS |
| `DLP_ENABLED` | Enable Cloud DLP | `False` | No |
| `PUBSUB_ENABLED` | Enable Pub/Sub events | `False` | No |
| `SMTP_HOST` | SMTP server for email alerts | `` | For alerts |
| `SMTP_PORT` | SMTP port | `587` | For alerts |
| `SMTP_USER` | SMTP username | `` | For alerts |
| `SMTP_PASSWORD` | SMTP password | `` | For alerts |
| `HIGH_RISK_THRESHOLD` | High risk score threshold | `71.0` | No |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Access token TTL | `15` | No |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token TTL | `7` | No |

---

## API Documentation

The full API is documented at `/docs` (Swagger UI) or `/redoc` (ReDoc) when the backend is running.

Base URL: `http://localhost:8000/api/v1`

### Endpoints Overview

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/auth/google-login` | Sign in with Google OAuth 2.0 | No |
| POST | `/auth/register` | Register a new user (legacy) | No |
| POST | `/auth/login` | Login and get tokens | No |
| POST | `/auth/refresh` | Refresh access token | No |
| GET | `/auth/me` | Get current user profile | Yes |
| POST | `/auth/change-password` | Change password | Yes |
| GET | `/users/` | List users (admin) | Admin |
| GET | `/users/{id}` | Get user details | Yes |
| PUT | `/users/{id}/role` | Update user role | Admin |
| DELETE | `/users/{id}` | Deactivate user | Admin |
| POST | `/files/upload` | Upload a file | Yes |
| GET | `/files` | List user files | Yes |
| GET | `/files/{id}` | Get file details | Yes |
| DELETE | `/files/{id}` | Delete a file | Yes |
| GET | `/files/{id}/download` | Download a file | Yes |
| POST | `/scans/start/{file_id}` | Start PII scan | Yes |
| GET | `/scans/file/{file_id}` | Get scan results | Yes |
| GET | `/scans/{id}` | Get single result | Yes |
| GET | `/scans/` | List all scans | Admin |
| GET | `/scans/risk/file/{file_id}` | Get risk assessment | Yes |
| GET | `/scans/risk/summary` | Get risk summary | Yes |
| POST | `/ai/recommend/{file_id}` | AI recommendations | Yes |
| POST | `/ai/summary/{file_id}` | AI summary | Yes |
| POST | `/ai/executive-report` | AI executive report | Yes |
| GET | `/dashboard/stats` | Dashboard statistics | Yes |
| GET | `/dashboard/trends` | Risk trends chart | Yes |
| GET | `/dashboard/distribution` | Risk distribution | Yes |
| GET | `/dashboard/compliance` | Compliance score | Yes |
| GET | `/alerts` | List alerts | Yes |
| GET | `/alerts/stats` | Alert statistics | Yes |
| PUT | `/alerts/{id}/read` | Mark alert read | Yes |
| PUT | `/alerts/read-all` | Mark all read | Yes |
| POST | `/reports/generate` | Generate report | Yes |
| GET | `/reports` | List reports | Yes |
| GET | `/reports/{id}` | Get report details | Yes |
| GET | `/reports/{id}/download` | Download PDF | Yes |
| GET | `/health` | Health check | No |

### Example API Calls

```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "email": "john@example.com", "password": "Secure@123"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "Admin@123"}'

# Upload file (replace TOKEN with actual JWT)
curl -X POST http://localhost:8000/api/v1/files/upload \
  -H "Authorization: Bearer TOKEN" \
  -F "file=@data.csv"

# Start scan
curl -X POST http://localhost:8000/api/v1/scans/start/FILE_ID \
  -H "Authorization: Bearer TOKEN"

# Get dashboard stats
curl http://localhost:8000/api/v1/dashboard/stats \
  -H "Authorization: Bearer TOKEN"

# Health check (no auth)
curl http://localhost:8000/api/v1/health
```

---

## Deployment

### Frontend (Vercel)

The frontend is deployed to Vercel. The `vercel.json` configuration handles SPA rewrites and build settings.

```bash
cd frontend
npx vercel --prod
```

Required environment variables (configure in Vercel dashboard):
- `VITE_API_URL`: Backend API URL (e.g., `https://privacy-platform.onrender.com/api/v1`)

### Backend (Render)

The backend is deployed to Render using the `render.yaml` Blueprint or the Render dashboard.

```bash
# Deploy using Blueprint
render blueprint apply

# Or via the Render dashboard:
# 1. Connect GitHub repository
# 2. Select the blueprint file
# 3. Set environment variables
```

### Database (Supabase / Render PostgreSQL)

- Option 1: Use the Render PostgreSQL database defined in `render.yaml`
- Option 2: Use Supabase for managed PostgreSQL with built-in auth

### Google Cloud (Terraform)

```bash
cd infrastructure/terraform

# Initialize Terraform
terraform init

# Review the plan
terraform plan -var="project_id=your-gcp-project"

# Apply infrastructure
terraform apply -var="project_id=your-gcp-project"
```

---

## Testing

```bash
# Backend tests
cd backend
pytest --cov=app -v

# With HTML coverage report
pytest --cov=app --cov-report=html -v

# Specific test file
pytest app/tests/api/test_auth_api.py -v

# Run with PostgreSQL service container (matches CI)
docker-compose -f infrastructure/docker/docker-compose.yml up -d postgres
cd backend
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/privacy_platform \
  SECRET_KEY=test-secret-key-12345 \
  pytest --cov=app -v
```

---

## Cloud Integration

### Google Cloud Storage

File uploads can be stored in GCS instead of local disk. Set `GCS_BUCKET_NAME` and `GOOGLE_CLOUD_PROJECT` in the environment and ensure the service account has `roles/storage.objectAdmin` on the bucket.

### Cloud DLP

The optional DLP integration augments the regex detection engine with Google's Cloud Data Loss Prevention API for enhanced PII identification. Enable with `DLP_ENABLED=True`.

### Pub/Sub

Event-driven processing is supported via Pub/Sub topics for scan events, completed scans, alerts, and report events. Enable with `PUBSUB_ENABLED=True`.

### Cloud Functions

The `cloud-functions/scan_trigger/` directory contains a Cloud Function template that can be deployed to orchestrate scans when files are uploaded to GCS:

```bash
cd cloud-functions/scan_trigger
gcloud functions deploy scan-trigger \
  --runtime python312 \
  --trigger-topic scan-events \
  --region us-central1
```

---

## License

This project is licensed under the MIT License. See the LICENSE file for details.

---

## Contributors

- **Harika** - Initial work and architecture

---

## Acknowledgments

- FastAPI for the async Python web framework
- SQLAlchemy for the ORM and database toolkit
- Ollama for local AI model serving
- Google Cloud for DLP, Storage, and Pub/Sh services
- React and Vite for the frontend tooling
