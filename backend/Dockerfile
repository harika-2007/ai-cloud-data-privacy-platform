FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies: gcc for building native Python packages, curl for health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl && \
    rm -rf /var/lib/apt/lists/*


# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create runtime directories
RUN mkdir -p uploads reports logs

EXPOSE 8000

# Use server:app (app is defined in server.py, not app.main)
# --reload is controlled by the DEBUG env var in server.py's __main__ block
# ${PORT:-8000} allows Render to inject its PORT environment variable
# Proxy headers middleware is applied in server.py's create_app() function
CMD sh -c "uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}"
