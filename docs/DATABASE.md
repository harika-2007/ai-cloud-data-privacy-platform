# Database Schema

## Overview

The platform uses PostgreSQL 15+ with SQLAlchemy 2.0 async ORM (asyncpg driver). The database schema consists of 7 core tables: `users`, `files`, `scan_results`, `risk_assessments`, `alerts`, `reports`, and `compliance_logs`.

### Entity Relationship Diagram

```
┌──────────────┐       ┌──────────────┐       ┌──────────────────┐
│    users     │1────N│    files     │1────N│  scan_results     │
│              │       │              │       │                  │
│  id (PK)     │       │  id (PK)     │       │  id (PK)          │
│  email (UQ)  │       │  user_id(FK) │       │  file_id (FK)     │
│  name        │       │  filename    │       │  pii_type         │
│  role        │       │  file_type   │       │  value (masked)   │
│  provider    │       │  file_size   │       │  confidence       │
│  password    │       │  status      │       │  severity         │
│  google_id   │       │  risk_score  │       │  line_number      │
│  is_active   │       │  uploaded_at │       │  context          │
│  created_at  │       │  scanned_at  │       │  created_at       │
└──────┬───────┘       └──────┬───────┘       └──────────────────┘
       │                      │
       │                      │ 1────1
       │                      │
       │              ┌───────┴──────────┐
       │              │ risk_assessments │
       │              │                  │
       │              │  id (PK)         │
       │              │  file_id (FK)    │
       │              │  risk_score      │
       │              │  risk_level      │
       │              │  breakdown (J)   │
       │              │  explanation     │
       │              │  created_at      │
       │              └──────────────────┘
       │
       │ 1────N       ┌──────────────┐
       ├─────────────│    alerts     │
       │             │              │
       │             │  id (PK)     │
       │             │  user_id(FK) │
       │             │  file_id(FK) │
       │             │  type        │
       │             │  severity    │
       │             │  title       │
       │             │  message     │
       │             │  is_read     │
       │             │  created_at  │
       │             └──────────────┘
       │
       │ 1────N       ┌──────────────┐
       ├─────────────│   reports     │
       │             │              │
       │             │  id (PK)     │
       │             │  file_id(FK) │
       │             │  user_id(FK) │
       │             │  type        │
       │             │  status      │
       │             │  pdf_path    │
       │             │  ai_summary  │
       │             │  created_at  │
       │             └──────────────┘
       │
       │ 1────N       ┌──────────────────┐
       └─────────────│ compliance_logs  │
                     │                  │
                     │  id (PK)         │
                     │  user_id(FK)     │
                     │  action          │
                     │  resource_type   │
                     │  resource_id     │
                     │  details (J)     │
                     │  ip_address      │
                     │  created_at      │
                     └──────────────────┘

(J) = JSON column
(FK) = Foreign Key
(PK) = Primary Key
(UQ) = Unique
```

---

## Table Definitions

### users

Stores user accounts for authentication and authorization.

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | UUID | PK, NOT NULL | `gen_random_uuid()` | Unique user identifier |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL | - | User email address (login) |
| `name` | VARCHAR(255) | NOT NULL | - | Display name |
| `password` | VARCHAR(255) | NULLABLE | - | bcrypt hashed password (NULL for Google users) |
| `role` | VARCHAR(20) | NOT NULL | `'user'` | RBAC role: `admin`, `analyst`, `user`, `viewer` |
| `provider` | VARCHAR(20) | NOT NULL | `'LOCAL'` | Auth provider: `LOCAL`, `GOOGLE` |
| `google_id` | VARCHAR(255) | UNIQUE, NULLABLE | - | Google account subject ID |
| `profile_picture` | TEXT | NULLABLE | - | URL to profile picture |
| `is_active` | BOOLEAN | NOT NULL | `true` | Whether account is active |
| `last_login` | TIMESTAMPTZ | NULLABLE | - | Last successful login timestamp |
| `created_at` | TIMESTAMPTZ | NOT NULL | `now()` | Account creation timestamp |
| `updated_at` | TIMESTAMPTZ | NOT NULL | `now()` | Last update timestamp |

**Indexes:**
- Primary key on `id`
- Unique index on `email`
- Unique index on `google_id`
- Index on `role`

---

### files

Stores metadata for uploaded files.

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | UUID | PK, NOT NULL | `gen_random_uuid()` | Unique file identifier |
| `user_id` | UUID | FK → users(id) ON DELETE CASCADE, NOT NULL | - | Owner of the file |
| `filename` | VARCHAR(255) | NOT NULL | - | Stored filename (UUID-prefixed) |
| `original_filename` | VARCHAR(255) | NOT NULL | - | Original upload filename |
| `file_type` | VARCHAR(10) | NOT NULL | - | `csv`, `xlsx`, `pdf`, `txt` |
| `mime_type` | VARCHAR(100) | NOT NULL | - | Detected MIME type |
| `file_size` | BIGINT | NOT NULL | - | File size in bytes |
| `storage_path` | VARCHAR(500) | NOT NULL | - | Local filesystem path |
| `gcs_path` | VARCHAR(500) | NULLABLE | - | GCS path (if cloud storage enabled) |
| `status` | VARCHAR(20) | NOT NULL | `'uploaded'` | Scan status: `uploaded`, `scanning`, `scanned`, `failed` |
| `risk_score` | FLOAT | NULLABLE | - | Overall risk score (0-100) |
| `risk_level` | VARCHAR(10) | NULLABLE | - | `LOW`, `MEDIUM`, `HIGH` |
| `findings_count` | INTEGER | NULLABLE | 0 | Total PII findings |
| `uploaded_at` | TIMESTAMPTZ | NOT NULL | `now()` | Upload timestamp |
| `scanned_at` | TIMESTAMPTZ | NULLABLE | - | Scan completion timestamp |
| `created_at` | TIMESTAMPTZ | NOT NULL | `now()` | Record creation timestamp |
| `updated_at` | TIMESTAMPTZ | NOT NULL | `now()` | Last update timestamp |

**Indexes:**
- Primary key on `id`
- Index on `user_id` (for user file listings)
- Index on `status` (for scan status queries)
- Index on `file_type` (for type filtering)
- Index on `risk_level` (for risk distribution queries)

---

### scan_results

Stores individual PII findings from file scans.

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | UUID | PK, NOT NULL | `gen_random_uuid()` | Unique result identifier |
| `file_id` | UUID | FK → files(id) ON DELETE CASCADE, NOT NULL | - | Scanned file |
| `pii_type` | VARCHAR(50) | NOT NULL | - | `aadhaar`, `pan`, `credit_card`, `email`, `phone` |
| `value` | TEXT | NOT NULL | - | Masked PII value found |
| `confidence` | FLOAT | NOT NULL | - | Detection confidence (0.0 - 1.0) |
| `severity` | VARCHAR(20) | NOT NULL | - | `critical`, `high`, `medium`, `low` |
| `line_number` | INTEGER | NULLABLE | - | Line/row number in file |
| `column_name` | VARCHAR(255) | NULLABLE | - | Column/field name |
| `context` | TEXT | NULLABLE | - | Surrounding context snippet |
| `created_at` | TIMESTAMPTZ | NOT NULL | `now()` | Record creation timestamp |

**Indexes:**
- Primary key on `id`
- Index on `file_id` (for scan result lookups)
- Index on `pii_type` (for PII type queries)
- Index on `severity` (for severity filtering)

---

### risk_assessments

Stores overall risk assessment for each scanned file (one-to-one with files).

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | UUID | PK, NOT NULL | `gen_random_uuid()` | Unique assessment identifier |
| `file_id` | UUID | FK → files(id) ON DELETE CASCADE, UNIQUE, NOT NULL | - | Assessed file |
| `risk_score` | FLOAT | NOT NULL | - | Composite risk score (0-100) |
| `risk_level` | VARCHAR(10) | NOT NULL | - | `LOW`, `MEDIUM`, `HIGH` |
| `breakdown` | JSONB | NOT NULL | `'{}'` | Score breakdown by PII type |
| `explanation` | TEXT | NULLABLE | - | Human-readable risk explanation |
| `created_at` | TIMESTAMPTZ | NOT NULL | `now()` | Assessment creation timestamp |

**Indexes:**
- Primary key on `id`
- Unique index on `file_id`
- Index on `risk_level` (for risk distribution queries)

**breakdown JSON Structure:**
```json
{
  "aadhaar_score": 150,
  "pan_score": 200,
  "credit_card_score": 120,
  "email_score": 30,
  "phone_score": 20,
  "total_score": 520,
  "severity_counts": {
    "critical": 5,
    "high": 5,
    "medium": 3,
    "low": 2
  },
  "findings_breakdown": {
    "aadhaar": 3,
    "pan": 5,
    "credit_card": 2,
    "email": 3,
    "phone": 2
  }
}
```

---

### alerts

Stores system-generated alerts for high-risk findings.

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | UUID | PK, NOT NULL | `gen_random_uuid()` | Unique alert identifier |
| `user_id` | UUID | FK → users(id) ON DELETE SET NULL | - | Alert recipient (NULL if user deleted) |
| `file_id` | UUID | FK → files(id) ON DELETE SET NULL | - | Related file (NULL if file deleted) |
| `type` | VARCHAR(50) | NOT NULL | - | `risk_threshold`, `new_scan`, `high_findings` |
| `severity` | VARCHAR(20) | NOT NULL | - | `critical`, `high`, `medium`, `low` |
| `title` | VARCHAR(255) | NOT NULL | - | Alert title |
| `message` | TEXT | NOT NULL | - | Alert message body |
| `is_read` | BOOLEAN | NOT NULL | `false` | Whether alert has been read |
| `read_at` | TIMESTAMPTZ | NULLABLE | - | When alert was marked read |
| `created_at` | TIMESTAMPTZ | NOT NULL | `now()` | Alert creation timestamp |

**Indexes:**
- Primary key on `id`
- Index on `user_id` (for user alert listings)
- Index on `is_read` (for unread count queries)
- Index on `severity` (for severity filtering)
- Index on `type` (for type filtering)

---

### reports

Stores generated compliance reports.

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | UUID | PK, NOT NULL | `gen_random_uuid()` | Unique report identifier |
| `user_id` | UUID | FK → users(id) ON DELETE CASCADE, NOT NULL | - | Report creator |
| `file_id` | UUID | FK → files(id) ON DELETE SET NULL | - | Related file |
| `type` | VARCHAR(50) | NOT NULL | - | `compliance`, `audit`, `executive` |
| `status` | VARCHAR(20) | NOT NULL | `'generating'` | `generating`, `completed`, `failed` |
| `title` | VARCHAR(255) | NOT NULL | - | Report title |
| `report_data` | JSONB | NULLABLE | - | Report content data |
| `pdf_path` | VARCHAR(500) | NULLABLE | - | Path to generated PDF |
| `file_size_kb` | INTEGER | NULLABLE | - | PDF file size |
| `ai_summary` | TEXT | NULLABLE | - | AI-generated executive summary |
| `generated_at` | TIMESTAMPTZ | NULLABLE | - | Generation completion time |
| `created_at` | TIMESTAMPTZ | NOT NULL | `now()` | Record creation timestamp |
| `updated_at` | TIMESTAMPTZ | NOT NULL | `now()` | Last update timestamp |

**Indexes:**
- Primary key on `id`
- Index on `user_id` (for user report listings)
- Index on `file_id` (for file-specific reports)
- Index on `status` (for pending report queries)

---

### compliance_logs

Stores audit trail for compliance-related actions.

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | UUID | PK, NOT NULL | `gen_random_uuid()` | Unique log identifier |
| `user_id` | UUID | FK → users(id) ON DELETE SET NULL | - | User who performed action |
| `action` | VARCHAR(50) | NOT NULL | - | Action performed: `file_upload`, `file_delete`, `scan_start`, `scan_complete`, `report_generate`, `report_download`, `login`, `logout`, `role_change`, `alert_read` |
| `resource_type` | VARCHAR(50) | NOT NULL | - | Type of resource: `file`, `scan`, `report`, `alert`, `user`, `auth` |
| `resource_id` | VARCHAR(255) | NULLABLE | - | ID of affected resource |
| `details` | JSONB | NULLABLE | - | Additional context (IP, user agent, etc.) |
| `ip_address` | VARCHAR(45) | NULLABLE | - | Client IP address |
| `created_at` | TIMESTAMPTZ | NOT NULL | `now()` | Log timestamp |

**Indexes:**
- Primary key on `id`
- Index on `user_id` (for user action history)
- Index on `action` (for action type queries)
- Index on `resource_type` (for resource type queries)
- Index on `created_at` (for time-range queries)

---

## Risk Scoring Logic

The risk score is calculated using the following weighted formula:

| PII Type | Weight per Occurrence | Max Contribution |
|----------|----------------------|-----------------|
| Aadhaar | 50 | 500 |
| PAN | 40 | 400 |
| Credit Card | 60 | 600 |
| Email | 10 | 100 |
| Phone | 10 | 100 |

**Risk Level Thresholds:**

| Level | Score Range |
|-------|-------------|
| LOW | 0 - 30 |
| MEDIUM | 31 - 70 |
| HIGH | 71 - 100 |

The composite score is normalized to 0-100 using:

```
total_weighted = sum(pii_type_count * weight_per_type)
risk_score = min(total_weighted / 10, 100)
```

---

## Migration Strategy

Migrations are managed with Alembic.

### Creating Migrations

```bash
cd backend

# Auto-generate migration from model changes
alembic revision --autogenerate -m "description_of_change"

# Review the generated migration
# File will be in alembic/versions/

# Apply migrations
alembic upgrade head

# Rollback one step
alembic downgrade -1

# View migration history
alembic history

# View current revision
alembic current
```

### Migration Guidelines

1. **Always review** autogenerated migrations before applying
2. **Test migrations** against a copy of production data
3. **Use `batch_mode`** for large tables to avoid locks
4. **Add indexes** for new query patterns
5. **Set appropriate defaults** for new columns on existing tables
6. **Use `server_default`** for timestamps rather than application defaults

### Seed Data

The project includes a seed script for demo data:

```bash
cd backend
python ../scripts/seed.py
```

This creates:
- Admin user (admin@example.com / Admin@123)
- Sample analyst and viewer users
- 5 sample uploaded files with scan results
- Sample risk assessments and alerts
- 2 sample compliance reports
