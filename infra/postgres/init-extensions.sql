-- Idempotent extension setup for a fresh PatchPilot database.
-- Migrations also guard vector with IF NOT EXISTS.
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
