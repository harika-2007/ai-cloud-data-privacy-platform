# Docker Setup Guide

## Prerequisites

- Docker Engine 24.0+ and Docker Compose v2.20+
- At least 8 GB RAM allocated to Docker (16 GB recommended for AI features)
- At least 10 GB free disk space

## Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd privacy-platform

# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

The application will be available at:
- **Frontend:** http://localhost:3000
- **API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Ollama:** http://localhost:11434

---

## Service Architecture

```
┌─────────────┐     ┌──────────────┐
│             │     │              │
│   Nginx     │────►│   Frontend   │
│   :80       │     │   (React)    │
│             │     │              │
└──────┬──────┘     └──────────────┘
       │
       │  /api/* → :8000
       ▼
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│             │     │              │     │              │
│   Backend   │────►│  PostgreSQL  │     │   Ollama     │
│   :8000     │     │  :5432       │     │  :11434      │
│   (FastAPI) │     │              │     │  (LLM)       │
│             │     └──────────────┘     │              │
└─────────────┘                          └──────────────┘
```

---

## Service Descriptions

### 1. PostgreSQL (postgres:16-alpine)

Database for all application data.

| Property | Value |
|----------|-------|
| Port | `5432` |
| Image | `postgres:16-alpine` |
| Health Check | `pg_isready -U privacy_user -d privacy_platform` |

**Volumes:**
- `postgres_data:/var/lib/postgresql/data` — Persistent database storage
- `./database/init.sql:/docker-entrypoint-initdb.d/init.sql` — Initialization script

**Environment Variables:**
| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_USER` | `privacy_user` | Database user |
| `POSTGRES_PASSWORD` | `privacy_pass_2024` | Database password |
| `POSTGRES_DB` | `privacy_platform` | Database name |

---

### 2. Backend (FastAPI)

Python FastAPI application with the PII detection engine.

| Property | Value |
|----------|-------|
| Port | `8000` |
| Build Context | `./backend` |
| Dockerfile | `./backend/Dockerfile` |
| Health Check | `curl -f http://localhost:8000/api/v1/health` |

**Volumes:**
- `./backend:/app` — Live code reloading in development
- `./uploads:/app/uploads` — Uploaded files storage
- `./reports:/app/reports` — Generated PDF reports
- `./logs:/app/logs` — Application logs

**Environment Variables:**
| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | AsyncPG connection string | PostgreSQL connection |
| `SECRET_KEY` | `super-secret-key...` | JWT signing key |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Token expiration |
| `OLLAMA_URL` | `http://host.docker.internal:11434` | Ollama endpoint |
| `OLLAMA_ENABLED` | `true` | Enable AI features |
| `ENVIRONMENT` | `development` | Environment mode |
| `CORS_ORIGINS` | `http://localhost:3000,...` | Allowed origins |
| `LOG_LEVEL` | `INFO` | Logging level |

---

### 3. Frontend (React + Vite)

React application served via Nginx.

| Property | Value |
|----------|-------|
| Port | `3000` (via Nginx) |
| Build Context | `./frontend` |
| Dockerfile | `./frontend/Dockerfile` |

**Volumes:**
- `./frontend:/app` — Live code reloading
- `/app/node_modules` — Named volume (avoids overwriting)

**Build Arguments:**
| Argument | Description |
|----------|-------------|
| `VITE_API_URL` | Backend API URL (`http://localhost:8000`) |

---

### 4. Nginx (Reverse Proxy)

Routes traffic between frontend and backend.

| Property | Value |
|----------|-------|
| Port | `80` |
| Image | `nginx:alpine` |

**Configuration:** `./nginx/nginx.conf`

**Volumes:**
- `./nginx/nginx.conf:/etc/nginx/conf.d/default.conf` — Nginx config
- `./frontend/dist:/usr/share/nginx/html` — Static files

**Route Mapping:**
| Path | Target |
|------|--------|
| `/` | Frontend (static files) |
| `/api/*` | Backend (:8000) |

---

### 5. Ollama (LLM Server)

AI model serving for compliance recommendations.

| Property | Value |
|----------|-------|
| Port | `11434` |
| Image | `ollama/ollama:latest` |
| Health Check | `ollama list` |

**Volumes:**
- `ollama_data:/root/.ollama` — Model storage

**Post-Start Setup:**
```bash
# After services are running, pull the default model
docker exec privacy-ollama ollama pull llama3

# Verify the model is available
docker exec privacy-ollama ollama list
```

---

## Environment Configuration

Create a `.env` file in the project root for custom configuration:

```ini
# Database
POSTGRES_USER=privacy_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=privacy_platform

# Security
SECRET_KEY=your-32-char-min-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# AI
OLLAMA_URL=http://host.docker.internal:11434
OLLAMA_ENABLED=true

# Google Cloud (optional)
GCS_BUCKET_NAME=your-bucket
DLP_ENABLED=false
PUBSUB_ENABLED=false

# OAuth (optional)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
```

---

## Common Commands

### Service Management

```bash
# Start all services
docker-compose up -d

# Start specific services
docker-compose up -d postgres backend

# Stop all services
docker-compose down

# Stop and remove volumes (destroys data)
docker-compose down -v

# Restart a specific service
docker-compose restart backend

# View logs
docker-compose logs -f
docker-compose logs -f backend
docker-compose logs -f postgres
```

### Database Operations

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U privacy_user -d privacy_platform

# Run a query
docker-compose exec postgres psql -U privacy_user -d privacy_platform -c "SELECT * FROM users;"

# Backup database
docker-compose exec postgres pg_dump -U privacy_user privacy_platform > backup.sql

# Restore database
cat backup.sql | docker-compose exec -T postgres psql -U privacy_user privacy_platform
```

### File Operations

```bash
# List uploaded files
docker-compose exec backend ls -la /app/uploads

# List generated reports
docker-compose exec backend ls -la /app/reports
```

### Ollama Operations

```bash
# Pull a specific model
docker exec privacy-ollama ollama pull llama3
docker exec privacy-ollama ollama pull qwen2:7b

# List available models
docker exec privacy-ollama ollama list

# Remove a model
docker exec privacy-ollama ollama rm llama3

# Test the model
docker exec privacy-ollama ollama run llama3 "Hello"
```

---

## Volumes

| Volume | Mount Point | Size Warning | Persistence |
|--------|-------------|-------------|-------------|
| `postgres_data` | `/var/lib/postgresql/data` | Grows with files | Survives `down` |
| `ollama_data` | `/root/.ollama` | 4-8 GB per model | Survives `down` |

---

## Health Checks

Each service includes a Docker health check:

| Service | Check | Interval | Timeout | Retries | Start Period |
|---------|-------|----------|---------|---------|-------------|
| PostgreSQL | `pg_isready` | 10s | 5s | 5 | 0s |
| Backend | `curl /health` | 30s | 10s | 3 | 15s |
| Ollama | `ollama list` | 30s | 10s | 3 | 40s |

---

## Troubleshooting

### Port Conflicts

```bash
# Check what's using a port
netstat -ano | findstr :8000   # Windows
lsof -i :8000                  # macOS/Linux

# Change port mapping in docker-compose.yml
ports:
  - "8001:8000"  # Map host 8001 to container 8000
```

### Container Connectivity

Services communicate via the `privacy-network` bridge network using service names as hostnames:
- Backend → `postgres:5432`
- Backend → `ollama:11434`
- Frontend → `backend:8000` (via Nginx)

If containers can't reach each other, verify they're on the same network:
```bash
docker network inspect privacy-platform_privacy-network
```

### Performance Issues

```bash
# Check container resource usage
docker stats

# Allocate more memory to Ollama
docker update --memory="4g" privacy-ollama

# If Ollama crashes, increase Docker memory in Docker Desktop settings
```

### Logs and Debugging

```bash
# Check all logs
docker-compose logs -f

# Check specific service
docker-compose logs backend

# Access container shell
docker-compose exec backend bash
docker-compose exec postgres sh

# Full reset (destroys data)
docker-compose down -v
docker-compose up -d
```

### Common Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| Backend won't start | DB not ready | Wait for PostgreSQL health check |
| File upload fails 413 | File too large | Increase MAX_UPLOAD_SIZE_MB in .env |
| AI returns empty | Ollama model not pulled | Run `docker exec privacy-ollama ollama pull llama3` |
| Port already in use | Another service on same port | Change port mapping in docker-compose.yml |
| "Host is unreachable" | Container network issue | Check `privacy-network` exists and services are attached |
