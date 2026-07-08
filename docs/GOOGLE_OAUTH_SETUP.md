# Google OAuth 2.0 Setup Guide

This guide walks you through configuring Google Sign-In for the SecureCloud AI platform.

## Overview

The application uses **Google Sign-In** via a server-side redirect flow:

1. User clicks **"Continue with Google"** on the login page
2. Browser is redirected to the backend at `/api/v1/auth/google/login`
3. Backend redirects the user to Google's OAuth 2.0 consent screen
4. User selects their Google account and consents
5. Google redirects back to the backend at `/api/v1/auth/google/callback`
6. Backend exchanges the authorization code for an ID token
7. A new user is auto-created in the database, or an existing user is logged in
8. Backend generates JWT access and refresh tokens
9. Backend redirects to the frontend at `/auth/callback` with tokens in URL params
10. The frontend stores the tokens and navigates to the dashboard

## Prerequisites

- A Google Cloud Platform account (free tier works)
- Access to the [Google Cloud Console](https://console.cloud.google.com/)
- A project where you can create OAuth credentials

## Step-by-Step Configuration

### 1. Create or Select a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Click the project dropdown at the top of the page
3. Click **New Project** (or select an existing one)
4. Enter a project name (e.g., "SecureCloud AI")
5. Click **Create**

### 2. Configure the OAuth Consent Screen

1. In the left sidebar, navigate to **APIs & Services** → **OAuth consent screen**
2. Select **External** user type (since this is for external users)
3. Click **Create**
4. Fill in the required fields:
   - **App name**: `SecureCloud AI`
   - **User support email**: Your email
   - **Developer contact information**: Your email
5. Click **Save and Continue**
6. **Scopes**: Click **Add or Remove Scopes**, then select:
   - `.../auth/userinfo.email` — View your email address
   - `.../auth/userinfo.profile` — View your basic profile info
   - `openid` — Associate you with your personal info
7. Click **Save and Continue**
8. **Test users**: Add your email address(es) for testing
9. Click **Save and Continue**
10. Review and click **Back to Dashboard**

> **Note**: If your app is in "Testing" mode, only test users can sign in. When you're ready for production, you can publish the app by clicking **Publish App** on the OAuth consent screen.

### 3. Create OAuth 2.0 Credentials

1. In the left sidebar, click **Credentials**
2. Click **+ Create Credentials** → **OAuth 2.0 Client ID**
3. Select **Web application** as the application type
4. Under **Name**, enter: `SecureCloud AI Web Client`
5. Under **Authorized JavaScript origins**, add:

   ```
   http://localhost:5173
   http://localhost:5174
   https://your-production-domain.com
   ```

6. Under **Authorized redirect URIs**, add:

   ```
   http://localhost:8000/api/v1/auth/google/callback
   https://your-production-domain.com
   ```

7. Click **Create**

### 4. Copy Your Credentials

After creation, a dialog appears with your credentials:

```
Client ID:     xxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.apps.googleusercontent.com
Client Secret: GOCSPX-xxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Copy both values.** You'll need them in the next step.

## Environment Configuration

### Backend (`backend/.env`)

Add these variables to `backend/.env`:

```ini
# Google OAuth 2.0
GOOGLE_CLIENT_ID=xxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxxxxxxxxxxxxxxxxx
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback
```

> **No frontend env variables needed.** The frontend uses a simple redirect link — no Google Identity Services SDK, no `VITE_GOOGLE_CLIENT_ID`.

## Verification

### Check Configuration Status

After restarting the services, check the backend logs:

- `INFO  Google OAuth is configured (client_id: xxxx...)` — correctly configured
- `WARNING  Google OAuth is NOT configured — To enable...` — missing `GOOGLE_CLIENT_ID`

### Test the Full Flow

1. Open the application at `http://localhost:5173`
2. Click **Continue with Google**
3. You are redirected to Google's account picker
4. Select your Google account
5. You should be redirected back to the application dashboard
6. Sign out
7. Sign in again with the same Google account
8. You should be logged in immediately (existing user detection)

### Verify the Database

```bash
# Connect to PostgreSQL and check the users table
SELECT id, name, email, provider, google_id, profile_picture
FROM users
WHERE provider = 'GOOGLE';
```

You should see your Google account with:
- `provider` = `GOOGLE`
- `google_id` populated
- `profile_picture` with your Google avatar URL

## Troubleshooting

| Problem | Likely Cause | Solution |
|---------|-------------|----------|
| `redirect_uri_mismatch` | Incorrect redirect URI in Google Cloud Console | Add `http://localhost:8000/api/v1/auth/google/callback` to Authorized redirect URIs |
| `Invalid issuer` error | Token verification fails | Ensure the backend `GOOGLE_CLIENT_ID` matches the Client ID in Google Cloud Console |
| Login redirects to `/login?error=...` | Backend OAuth error | Check the error parameter and backend logs for details |
| OAuth returns to login page | Backend not running or CORS | Check backend is running on port 8000 and CORS origins include the frontend URL |
| User already exists with different provider | Email used with password login first | Sign in with email/password instead, or contact admin |

## Production Deployment

For production, update the authorized origins and URIs:

```ini
# Google Cloud Console → Authorized redirect URIs
https://your-backend-domain.com/api/v1/auth/google/callback

# Environment variables
GOOGLE_REDIRECT_URI=https://your-backend-domain.com/api/v1/auth/google/callback
CORS_ORIGINS=https://your-frontend-domain.com
```

Then publish your OAuth consent screen from **Testing** to **Production** mode.

## Architecture

```
┌──────────────┐     Redirect to          ┌──────────────┐
│              │  ───────────────────────► │              │
│   Browser    │   /api/v1/auth/google/   │   FastAPI    │
│  (Frontend)  │   login                  │   Backend    │
│              │                           │              │
│              │◄──────────────────────────│              │
│              │  302 → accounts.google.com│              │
└──────┬───────┘                           └──────┬───────┘
       │                                          │
       │  User selects account                    │  Code exchange
       │  at Google consent screen                │  + token verification
       │                                          │
       ▼                                          ▼
┌─────────────────────┐              ┌─────────────────────┐
│   Google OAuth      │◄─────────────│   Google Token API  │
│   Consent Screen    │   auth code   │   oauth2.googleapis │
└─────────────────────┘              └─────────────────────┘
       │
       │  Redirect to
       │  /api/v1/auth/google/callback?code=...
       ▼
┌──────────────┐
│   FastAPI    │  Verifies token, creates/updates user
│   Backend    │  Generates JWT tokens
└──────┬───────┘
       │
       │  Redirect to /auth/callback?access_token=...&refresh_token=...
       ▼
┌──────────────┐
│   Browser    │  Stores tokens, navigates to /dashboard
└──────────────┘
```
