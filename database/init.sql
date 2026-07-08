-- Initial database setup for Privacy Compliance Platform
-- This script runs on first PostgreSQL container startup

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Optional: create the application schema if using schema-based isolation
-- CREATE SCHEMA IF NOT EXISTS privacy;
