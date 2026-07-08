# Setup Guide

## Prerequisites Installation

### Python 3.12+

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-dev
```

**macOS (Homebrew):**
```bash
brew install python@3.12
```

**Windows:**
Download from [python.org](https://www.python.org/downloads/) and ensure "Add Python to PATH" is checked during installation.

### Node.js 18+

**Using nvm (recommended):**
```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
nvm install 18
nvm use 18
```

**Alternative (direct):**
Download from [nodejs.org](https://nodejs.org/)

### PostgreSQL 15+

**Ubuntu/Debian:**
```bash
sudo apt install postgresql-15
sudo systemctl start postgresql
```

**macOS:**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Windows:**
Download from [postgresql.org](https://www.postgresql.org/download/windows/)

### Docker & Docker Compose

Download from [docker.com](https://www.docker.com/products/docker-desktop/)

### Ollama (for AI Features)

```bash
# macOS / Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows
# Download from https://ollama.com/download

# Pull the default model
ollama pull llama3
```

---

## Backend Configuration

### 1. Create Virtual Environment

```bash
cd backend

# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate

# Windows
python -m venv .venv
.venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
cp .env.example .env
```

Edit the `.env` file with your configuration:

```ini
# Application
SECRET_KEY=your-secure-secret-key-at-least-32-characters-long
ENVIRONMENT=development
DEBUG=True
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/privacy_platform
DATABASE_SYNC_URL=postgresql://postgres:password@localhost:5432/privacy_platform

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Ollama / AI
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
AI_ENABLED=True

# File Upload
MAX_UPLOAD_SIZE_MB=50

# Google Cloud (optional)
GOOGLE_CLOUD_PROJECT=
GCS_BUCKET_NAME=
DLP_ENABLED=False
PUBSUB_ENABLED=False
```

### 4. Create the Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create the database
CREATE DATABASE privacy_platform;

# Exit
\q
```

### 5. Run Database Migrations

```bash
cd backend
alembic upgrade head
```

### 6. Seed Demo Data (Optional)

```bash
cd backend
python ../scripts/seed.py
```

### 7. Start the Backend Server

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`
API documentation at `http://localhost:8000/docs`

---

## Frontend Configuration

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

Create a `.env` file in the `frontend/` directory:

```ini
VITE_API_URL=http://localhost:8000/api/v1
```

### 3. Start the Development Server

```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

### 4. Build for Production

```bash
npm run build
```

Output will be in the `dist/` directory.

---

## Docker Setup

### Using Docker Compose (Full Stack)

```bash
# Start all services
cd infrastructure/docker
docker-compose up -d

# This will start:
# - PostgreSQL on port 5432
# - Backend API on port 8000
# - Frontend on port 80
# - Ollama on port 11434

# Pull the AI model (first time only, after services are up)
docker exec -it privacy-ollama ollama pull llama3

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs backend
docker-compose logs frontend

# Stop all services
docker-compose down

# Stop and remove volumes (destroys data)
docker-compose down -v
```

### Building Individual Services

```bash
# Build backend only
docker build -t privacy-backend ./backend

# Build frontend only
docker build -t privacy-frontend ./frontend

# Run backend with local postgres
docker run -p 8000:8000 --env-file backend/.env privacy-backend
```

---

## Cloud Services Setup

### Google Cloud Platform

#### Prerequisites

1. Create a GCP project:
   ```bash
   gcloud projects create YOUR-PROJECT-ID --name="Privacy Platform"
   gcloud config set project YOUR-PROJECT-ID
   ```

2. Enable billing for the project.

3. Authenticate the gcloud CLI:
   ```bash
   gcloud auth application-default login
   ```

#### Storage Bucket

```bash
# Create the bucket
gsutil mb gs://privacy-platform-uploads

# Set environment variable
export GCS_BUCKET_NAME=privacy-platform-uploads
export GOOGLE_CLOUD_PROJECT=YOUR-PROJECT-ID
```

#### Cloud DLP

```bash
# Enable the DLP API
gcloud services enable dlp.googleapis.com

# Enable in the application
export DLP_ENABLED=True
```

#### Pub/Sub

```bash
# Enable Pub/Sub API
gcloud services enable pubsub.googleapis.com

# Create topics
gcloud pubsub topics create scan-events
gcloud pubsub topics create scan-completed
gcloud pubsub topics create alert-events
gcloud pubsub topics create report-events

# Enable in the application
export PUBSUB_ENABLED=True
```

#### Service Account

```bash
# Create a service account for the backend
gcloud iam service-accounts create privacy-app-backend \
  --display-name="Privacy Platform Backend"

# Grant storage admin
gsutil iam ch serviceAccount:privacy-app-backend@PROJECT-ID.iam.gserviceaccount.com:roles/storage.objectAdmin \
  gs://privacy-platform-uploads

# Grant DLP user
gcloud projects add-iam-policy-binding PROJECT-ID \
  --member="serviceAccount:privacy-app-backend@PROJECT-ID.iam.gserviceaccount.com" \
  --role="roles/dlp.user"

# Create and download key
gcloud iam service-accounts keys create credentials.json \
  --iam-account=privacy-app-backend@PROJECT-ID.iam.gserviceaccount.com
export GOOGLE_APPLICATION_CREDENTIALS=./credentials.json
```

### Using Terraform (Automated)

```bash
cd infrastructure/terraform

# Initialize
terraform init

# Preview changes
terraform plan -var="project_id=YOUR_PROJECT_ID" -var="environment=development"

# Apply
terraform apply -var="project_id=YOUR_PROJECT_ID" -var="environment=development" -auto-approve

# Destroy (when no longer needed)
terraform destroy -var="project_id=YOUR_PROJECT_ID" -auto-approve
```

---

## Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest --cov=app -v

# Run with verbose coverage report
pytest --cov=app --cov-report=term-missing -v

# Generate HTML coverage report
pytest --cov=app --cov-report=html -v
# Open htmlcov/index.html in browser

# Run specific test file
pytest app/tests/api/test_auth_api.py -v

# Run specific test class
pytest app/tests/api/test_auth_api.py::TestRegister -v

# Run with PostgreSQL service container
docker-compose -f infrastructure/docker/docker-compose.yml up -d postgres
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/privacy_platform \
  SECRET_KEY=test-secret-key-12345 \
  pytest --cov=app -v
```

### Frontend Tests

```bash
cd frontend

# Lint check
npm run lint

# Build check
npm run build
```

---

## CI/CD Pipeline

### GitHub Actions

The repository includes two GitHub Actions workflows:

**1. Test Workflow** (`.github/workflows/test.yml`)
- Triggered on pull requests to `main`
- Runs backend tests with PostgreSQL service container
- Runs frontend lint and build checks

**2. Deploy Workflow** (`.github/workflows/deploy.yml`)
- Triggered on pushes to `main`
- Runs tests
- Builds and pushes Docker images to Docker Hub
- Deploys backend to Render
- Deploys frontend to Vercel

### Required GitHub Secrets

| Secret | Description |
|--------|-------------|
| `DOCKER_USERNAME` | Docker Hub username |
| `DOCKER_PASSWORD` | Docker Hub password or access token |
| `RENDER_API_KEY` | Render API key for deployments |
| `RENDER_SERVICE_ID` | Render backend service ID |
| `VERCEL_TOKEN` | Vercel access token |

---

## Troubleshooting

### Database Issues

**Problem:** Cannot connect to PostgreSQL
**Solution:**
```bash
# Check if PostgreSQL is running
pg_isready

# Start PostgreSQL
sudo systemctl start postgresql   # Linux
brew services start postgresql@15 # macOS

# Verify DATABASE_URL in .env
echo $DATABASE_URL
```

**Problem:** Alembic migration fails
**Solution:**
```bash
cd backend
# Check migration status
alembic current

# View SQL of pending migrations
alembic upgrade head --sql

# Force a specific revision
alembic upgrade <revision_id>
```

### Ollama / AI Issues

**Problem:** AI recommendations return empty or timeout
**Solution:**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Pull the model explicitly
ollama pull llama3

# Check OLLAMA_BASE_URL in .env matches the running service
# When using Docker, it should be: http://ollama:11434
# When running locally, it should be: http://localhost:11434
```

**Problem:** Ollama container exits immediately
**Solution:**
```bash
# Run with more memory
docker run -d --memory="4g" -p 11434:11434 --name ollama ollama/ollama
```

### File Upload Issues

**Problem:** File upload fails with 413
**Solution:** The file exceeds `MAX_UPLOAD_SIZE_MB`. Increase the limit in `.env`:
```ini
MAX_UPLOAD_SIZE_MB=100
```

**Problem:** Unsupported file type
**Solution:** Only CSV, XLSX, PDF, and TXT files are supported. Check `ALLOWED_EXTENSIONS` in the settings.

### CORS Issues

**Problem:** Frontend cannot reach the API
**Solution:** Ensure `CORS_ORIGINS` includes the frontend URL:
```ini
CORS_ORIGINS=http://localhost:5173,http://localhost:3000,https://your-domain.com
```

### Docker Issues

**Problem:** Port already in use
**Solution:**
```bash
# Find what's using the port
netstat -ano | findstr :8000   # Windows
lsof -i :8000                  # Linux/macOS

# Change the port mapping in docker-compose.yml
ports:
  - "8001:8000"  # Map host 8001 to container 8000
```

**Problem:** Docker containers can't reach each other
**Solution:** Ensure all services are on the same network (`app-network`) and use service names (e.g., `postgres`, not `localhost`).

### General Debugging

```bash
# Check backend logs
docker-compose logs -f backend

# Check database logs
docker-compose logs -f postgres

# Access database shell
docker-compose exec postgres psql -U postgres -d privacy_platform

# Access backend shell
docker-compose exec backend bash

# Reset everything (destroys data)
docker-compose down -v
docker-compose up -d
```
