#!/bin/bash
set -e

echo "=== Privacy Platform Setup ==="
echo ""

# Check Python version
python3 --version || { echo "Python 3 required"; exit 1; }

# Create virtual environment
echo ">>> Creating virtual environment..."
cd "$(dirname "$0")/../backend"
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
echo ">>> Installing Python dependencies..."
pip install -r requirements.txt

# Setup environment
echo ">>> Setting up environment..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env from .env.example - please update with your settings"
fi

# Setup frontend
echo ">>> Installing frontend dependencies..."
cd ../frontend
npm install

# Setup Docker services
echo ">>> Starting Docker services..."
cd ../infrastructure/docker
docker-compose up -d postgres ollama

# Wait for database
echo ">>> Waiting for database..."
sleep 5

# Run migrations
echo ">>> Running database migrations..."
cd ../../backend
alembic upgrade head || echo "Migrations may have already run"

# Seed data
echo ">>> Seeding development data..."
python scripts/seed.py

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Start the backend:  cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo "Start the frontend: cd frontend && npm run dev"
echo "Access the app:    http://localhost:5173"
echo "API docs:          http://localhost:8000/docs"
echo ""
echo "Default credentials: admin@example.com / Admin@123"
