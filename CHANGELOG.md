# Changelog

> All notable changes to the Privacy Compliance Platform (SecureCloud AI).

---

## [1.1.0] — 2026-07-08

### Summary

Major refactor to enable the application to work correctly **through ngrok, Docker Compose, and production deployments (Render, Vercel)** without hardcoded localhost URLs. The core issue was Google OAuth requiring exact `redirect_uri` matching and the app being configured with fixed localhost references throughout.

### Modified Files (18)

| File | Change | Severity |
|------|--------|----------|
| `backend/server.py` | Dynamic CORS origins with auto-inclusion of localhost variants & regex wildcard support | 🔴 Critical |
| `backend/app/core/config/settings.py` | Added `NGROK_URL`, `PUBLIC_URL`, `SECURE_COOKIES`, `cors_origins_list`, `use_cors_wildcard` properties | 🔴 Critical |
| `backend/app/api/v1/auth/routes.py` | Dynamic Google OAuth redirect URI generation; secure cookie detection; URL fragment token delivery | 🔴 Critical |
| `frontend/src/pages/OAuthCallback.jsx` | Parse tokens from URL fragment `#` instead of query params `?` (security) | 🟠 High |
| `frontend/src/pages/Login.jsx` | Changed Google OAuth from absolute `http://localhost:8000/...` to relative `/api/v1/...` | 🔴 Critical |
| `frontend/nginx.conf` | `server_name _` catch-all; CORS headers; OPTIONS preflight; X-Forwarded-Proto/Host | 🔴 Critical |
| `frontend/src/services/api.js` | `withCredentials: true`; fixed 401 interceptor auth-endpoint exclusion | 🟠 High |
| `frontend/src/utils/constants.js` | `API_BASE_URL` defaults to `/api/v1` (relative) when `VITE_API_URL` unset | 🟠 High |
| `frontend/vite.config.js` | Dynamic proxy target from `VITE_API_URL` | 🟢 Medium |
| `frontend/Dockerfile` | Added `VITE_GOOGLE_CLIENT_ID` build arg | 🟢 Medium |
| `frontend/.env.example` | Documented `VITE_API_URL` (empty default), added `VITE_GOOGLE_CLIENT_ID` | 🟢 Medium |
| `nginx/default.conf` | `server_name _` catch-all; `X-Forwarded-Host` propagation | 🟠 High |
| `backend/Dockerfile` | Removed `--reload` from production CMD | 🟢 Medium |
| `backend/.env.example` | Full documentation: NGROK_URL, PUBLIC_URL, SECURE_COOKIES, dynamic GOOGLE_REDIRECT_URI, JWT settings | 🟢 Medium |
| `.env.example` | Added NGROK_URL, PUBLIC_URL, SECURE_COOKIES sections | 🟢 Medium |
| `docker-compose.yml` | Added NGROK_URL, PUBLIC_URL, SECURE_COOKIES env vars; VITE_API_URL build arg | 🟠 High |
| `docker-compose.override.yml` | Updated CORS_ORIGINS with 127.0.0.1; empty VITE_API_URL for nginx proxy | 🟠 High |
| `render.yaml` | Fixed `startCommand` to use `server:app`; added google OAuth + ngrok env vars | 🔴 Critical |

### 🔴 Critical Fixes

#### 1. Google OAuth Redirect URI — Dynamic Generation

**Before:** Hardcoded redirect URI in `backend/.env`:
```python
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback
```

**After:** Dynamically generated from request headers with env var overrides:
```python
def get_google_redirect_uri(request: Request) -> str:
    if settings.GOOGLE_REDIRECT_URI:
        return settings.GOOGLE_REDIRECT_URI  # explicit override
    base = get_base_url(request)              # from NGROK_URL, PUBLIC_URL, or headers
    return f"{base}/api/v1/auth/google/callback"
```

**Why:** Google OAuth requires an exact redirect URI match. With ngrok, the URL is `https://abc123.ngrok-free.app/...`, not `http://localhost:8000/...`. The URI must match exactly what's registered in Google Cloud Console.

**Setup:** Register these redirect URIs in Google Cloud Console:
- `http://localhost:8000/api/v1/auth/google/callback` (local dev)
- `http://localhost:80/api/v1/auth/google/callback` (Docker/nginx)
- `https://your-subdomain.ngrok-free.app/api/v1/auth/google/callback` (ngrok)
- `https://your-app.onrender.com/api/v1/auth/google/callback` (Render)

#### 2. Frontend OAuth Login URL — Relative Path

**Before:** Hardcoded absolute URL:
```javascript
window.location.assign('http://localhost:8000/api/v1/auth/google/login')
```

**After:** Relative path:
```javascript
window.location.assign('/api/v1/auth/google/login')
```

**Why:** The absolute URL forces the browser to `localhost:8000` regardless of environment. The relative URL works through Vite dev proxy, Docker nginx proxy, and production reverse proxy seamlessly.

#### 3. Dynamic Base URL Detection

Added `get_base_url()` that checks (in priority order):
1. `NGROK_URL` env var (explicit ngrok tunnel URL)
2. `PUBLIC_URL` env var (custom domain / Render)
3. `X-Forwarded-Proto` + `X-Forwarded-Host` headers (set by nginx/reverse proxy)
4. Direct request `Host` header (fallback)

#### 4. CORS Origins — Dynamic Configuration

**Before:** Static list in `.env`:
```
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

**After:** `server.py` auto-includes all localhost variants and supports `*` wildcard in dev mode:
```python
def get_cors_origins() -> list[str]:
    origins = settings.cors_origins_list
    if settings.use_cors_wildcard:
        return ["*"]
    # Auto-append all localhost variants
    localhost_patterns = ["http://localhost:3000", ..., "http://127.0.0.1:8000"]
    for origin in localhost_patterns:
        if origin not in origins:
            origins.append(origin)
    return origins
```

#### 5. Nginx `server_name` — Catch-All

**Before:** `server_name localhost;` — only responded to `Host: localhost` headers. ngrok sends a different hostname, so nginx returned 400.

**After:** `server_name _;` — accepts any hostname, including ngrok domains.

#### 6. Render.yaml `startCommand`

**Before:** `uvicorn app.main:app` — the FastAPI app is in `server.py`, not `app/main.py`.

**After:** `uvicorn server:app` — matches the actual application entry point.

### 🟠 Security Fixes

#### 1. OAuth Token Delivery via URL Fragment

**Before:** Tokens passed in query string `?access_token=...` — logged by nginx/infrastructure, visible in browser history.

**After:** Tokens passed in URL fragment `#access_token=...` — never sent to servers, cleared from URL after parsing.

#### 2. Secure Cookie Detection

**Before:** Cookie `secure=False` hardcoded — cookies marked non-secure even over HTTPS/ngrok, causing browser rejection.

**After:** `should_use_secure_cookie()` dynamically returns `True` when:
- `SECURE_COOKIES=True` env var is set
- `ENVIRONMENT=production`
- Request is over HTTPS (`X-Forwarded-Proto: https`)
- `NGROK_URL` is set (ngrok always uses HTTPS)

#### 3. OAuth State Cookie — Proper Flags

The `google_oauth_state` CSRF cookie now uses:
- `httponly=True` (was already)
- `secure=True` when appropriate (dynamically detected)
- `samesite="lax"` (was already)

#### 4. Cross-Origin CORS Headers

**Before:** Frontend nginx provided no CORS headers.

**After:** Frontend nginx now sends:
- `Access-Control-Allow-Origin: $http_origin` (dynamic)
- `Access-Control-Allow-Credentials: true`
- Full OPTIONS preflight handler returning 204

### 🟢 Configuration Improvements

#### Environment Variables Added

| Variable | Default | Purpose |
|----------|---------|---------|
| `NGROK_URL` | empty | ngrok tunnel URL override |
| `PUBLIC_URL` | empty | Custom domain / Render URL |
| `SECURE_COOKIES` | false | Force secure cookie flag |
| `GOOGLE_REDIRECT_URI` | empty | Auto-generated if empty |
| `JWT_ALGORITHM` | HS256 | JWT signing algorithm |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | 30 | Access token TTL |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | 7 | Refresh token TTL |
| `VITE_GOOGLE_CLIENT_ID` | empty | Google OAuth client ID for frontend |

#### Docker Compose Updates

- `docker-compose.yml`: Added `NGROK_URL`, `PUBLIC_URL`, `SECURE_COOKIES`, `VITE_API_URL` build arg
- `docker-compose.override.yml`: Updated `CORS_ORIGINS` with `127.0.0.1` variants; empty `VITE_API_URL` for nginx proxy

---

## Deployment Guide

### Local Development (Vite)

```bash
# Terminal 1 — Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # Edit with your values
uvicorn server:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 — Frontend
cd frontend
npm install
cp .env.example .env
npm run dev
# Opens at http://localhost:5173
```

### Docker Compose (Local)

```bash
cd privacy-platform
docker compose up --build
# Frontend: http://localhost:3000
# Backend:  http://localhost:8000
# Docs:     http://localhost:8000/docs
```

### Docker Compose with ngrok

```bash
# 1. Register your ngrok URL in Google Cloud Console as authorized redirect URI:
#    https://your-subdomain.ngrok-free.app/api/v1/auth/google/callback

# 2. Start ngrok:
ngrok http 80

# 3. Set NGROK_URL and start services:
$env:NGROK_URL="https://your-subdomain.ngrok-free.app"
docker compose up --build

# 4. Access at: https://your-subdomain.ngrok-free.app
```

### Docker Compose without nginx (direct backend access)

```bash
# If you don't need nginx, start just postgres and backend:
docker compose up postgres backend
# Access API at http://localhost:8000/docs
```

### Production — Render (Backend)

1. Fork/push repo to GitHub
2. In Render Dashboard → Blueprint → Connect repo
3. **Set these env vars in Render Dashboard** (marked `sync: false` in render.yaml):
   - `SECRET_KEY` — generate with `openssl rand -hex 32`
   - `GOOGLE_CLIENT_ID` — from Google Cloud Console
   - `GOOGLE_CLIENT_SECRET` — from Google Cloud Console
4. **Register these redirect URIs in Google Cloud Console:**
   - `https://your-app.onrender.com/api/v1/auth/google/callback`
5. Deploy: Render auto-detects `render.yaml`

### Production — Vercel (Frontend)

1. Import your frontend repo in Vercel
2. Set these env vars:
   - `VITE_API_URL=https://your-backend.onrender.com/api/v1`
3. `vercel.json` handles SPA routing via rewrites
4. **Set CORS_ORIGINS on Render:** `https://your-app.vercel.app`

---

## Testing Checklist

### Authentication Flows
- [ ] Email/password register and login
- [ ] JWT access token refresh
- [ ] Google OAuth sign-in (local dev)
- [ ] Google OAuth through ngrok
- [ ] Logout — tokens cleared
- [ ] Protected routes redirect to login

### API Endpoints
- [ ] `GET /api/v1/health` — returns 200
- [ ] `POST /api/v1/auth/register` — creates user
- [ ] `POST /api/v1/auth/login` — returns tokens
- [ ] `POST /api/v1/auth/refresh` — refreshes tokens
- [ ] `GET /api/v1/auth/me` — returns user profile

### CORS
- [ ] Frontend at localhost:5173 can reach backend at localhost:8000
- [ ] Frontend at localhost:3000 (Docker nginx) can reach backend
- [ ] ngrok frontend can reach backend through nginx proxy
- [ ] No CORS errors in browser console

### Docker
- [ ] `docker compose up --build` starts all services
- [ ] Health checks pass (postgres, backend)
- [ ] Frontend loads at http://localhost:3000
- [ ] API accessible through /api/v1/ endpoints
- [ ] File uploads work within 50MB limit

### Security
- [ ] JWT tokens delivered via URL fragment (`#`) not query params (`?`)
- [ ] Cookies use `Secure` flag when over HTTPS
- [ ] Cookies use `httponly` and `samesite=lax`
- [ ] CORS origins restricted (not `*` in production)
- [ ] `SECRET_KEY` changed from default in production
- [ ] `.env` files in `.gitignore`
- [ ] No hardcoded secrets in tracked files

---

## Production Checklist

### Before Going Live
- [ ] Generate strong `SECRET_KEY` (`openssl rand -hex 32`)
- [ ] Set `ENVIRONMENT=production`
- [ ] Set `DEBUG=false`
- [ ] Set `LOG_LEVEL=INFO`
- [ ] Set `SECURE_COOKIES=true`
- [ ] Register all production URLs in Google Cloud Console
- [ ] Generate new OAuth 2.0 Client ID for production (don't reuse dev)
- [ ] Set up production PostgreSQL (Supabase, Render, or RDS)
- [ ] Configure `CORS_ORIGINS` with exact production frontend URL
- [ ] Set up SSL/TLS certificate for custom domain
- [ ] Enable DLP and Pub/Sub if using GCP
- [ ] Set up monitoring and alerting

### Security Checklist
- [ ] All secrets managed via environment variables (not code)
- [ ] CORS restricted to known origins in production
- [ ] Rate limiting on auth endpoints
- [ ] Input validation on all endpoints (FastAPI/Pydantic handles this)
- [ ] SQL injection prevention (SQLAlchemy ORM handles this)
- [ ] XSS prevention (React handles this)
- [ ] CSRF protection via OAuth state parameter
- [ ] JWT tokens with short expiry (30 min access, 7 day refresh)
- [ ] HTTPS enforced everywhere
- [ ] File upload size and type validation
- [ ] Regular dependency updates (npm audit, pip audit)

---

## Architecture Notes

### Request Flow (Docker Compose)

```
Browser → :80 (nginx) → /api/* → backend:8000 (FastAPI)
                       → /*     → frontend:80 (nginx → SPA)
```

### Request Flow (ngrok)

```
ngrok → nginx:80 → /api/* → backend:8000
                 → /*     → frontend:80 → SPA
```

### Request Flow (Vercel + Render)

```
Browser → Vercel (SPA) → /api/v1/* → Render (FastAPI)
                       → /*        → SPA fallback (index.html)
```

### OAuth Flow

```
User clicks "Sign in with Google"
  → GET /api/v1/auth/google/login
  → Backend generates dynamic redirect_uri from request
  → Redirects to accounts.google.com with all params
  → User consents
  → Google redirects to /api/v1/auth/google/callback with ?code=...
  → Backend exchanges code for tokens
  → Backend creates/updates user in DB
  → Backend generates JWT tokens
  → Redirects to /auth/callback#access_token=...&refresh_token=...
  → Frontend OAuthCallback parses fragment, stores tokens
  → Redirects to /dashboard
```
