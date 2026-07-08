# AI-Powered Cloud Data Privacy Compliance & Security Monitoring Platform

## Project Overview
A cloud-native platform for detecting sensitive data (Aadhaar, PAN, Email, Phone, Credit Cards), assessing privacy risks, providing AI-generated compliance recommendations, generating reports, and monitoring compliance through a centralized dashboard.

## Tech Stack
- **Frontend**: React 18, Vite, TailwindCSS, Chart.js, React Router
- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.0, Pydantic v2
- **Database**: PostgreSQL 15+ (Supabase)
- **Auth**: JWT (access + refresh tokens), bcrypt
- **AI**: Ollama (Llama 3 / Qwen)
- **Cloud**: GCS, Cloud DLP, Pub/Sub
- **Deployment**: Docker, GitHub Actions, Vercel (FE), Render (BE)

## Project Structure
```
privacy-platform/
├── backend/
│   ├── app/
│   │   ├── api/v1/        # API routes (auth, files, scans, reports, alerts, dashboard, ai, health)
│   │   ├── core/           # Config, database, security
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   ├── repositories/   # Data access layer
│   │   ├── utils/          # Helpers, exceptions, logging
│   │   └── tests/          # Test suite
│   ├── alembic/            # DB migrations
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API client services
│   │   ├── hooks/          # Custom hooks
│   │   ├── context/        # Auth context
│   │   └── utils/          # Constants
│   ├── package.json
│   └── Dockerfile
├── infrastructure/         # Docker compose, GitHub Actions, Terraform
├── docs/                   # Documentation
├── cloud-functions/        # GCP Cloud Functions
└── scripts/                # Setup and seed scripts
```

## Key Architecture Decisions
- **Repository-Service Pattern**: Clean separation of data access and business logic
- **Async Everything**: FastAPI + asyncpg for non-blocking database operations
- **Repository Pattern**: BaseRepository<ModelType> generic CRUD, module-specific repos extend it
- **Pydantic v2**: All request/response validation via models
- **Clean Architecture**: Presentation → Service → Repository → Domain layers

## Environment Variables (.env)
- `SECRET_KEY`: JWT signing key (min 32 chars)
- `DATABASE_URL`: PostgreSQL async connection string
- `GOOGLE_CLOUD_PROJECT`: GCP project ID
- `OLLAMA_BASE_URL`: Ollama API endpoint
- `DLP_ENABLED`: Toggle Cloud DLP integration
- `AI_ENABLED`: Toggle AI recommendations

## Common Commands
```bash
# Backend
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd frontend && npm install && npm run dev

# Docker
docker-compose -f infrastructure/docker/docker-compose.yml up

# Tests
cd backend && pytest --cov=app -v

# Migrations
cd backend && alembic init alembic
alembic revision --autogenerate -m "init"
alembic upgrade head
```

## API Endpoints (prefix: /api/v1)
- Auth: POST /auth/register, POST /auth/login, POST /auth/refresh, GET /auth/me
- Files: POST /files/upload, GET /files, GET /files/{id}, DELETE /files/{id}
- Scans: POST /scans/start/{file_id}, GET /scans/file/{file_id}, GET /scans/risk/file/{file_id}
- AI: POST /ai/recommend/{file_id}, POST /ai/summary/{file_id}
- Dashboard: GET /dashboard/stats, GET /dashboard/trends
- Alerts: GET /alerts, PUT /alerts/{id}/read
- Reports: POST /reports/generate, GET /reports, GET /reports/{id}/download
- Health: GET /health
