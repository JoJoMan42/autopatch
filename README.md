# PatchPilot (AutoPatch)

> **AI-Assisted Secure Code Repair Platform**  
> Educational research prototype that transforms SAST vulnerability findings (SARIF) into reviewed, validated, and tested code fixes with human-in-the-loop approval.

---

## Architecture & Features

- **Automated SAST Ingestion**: Ingests and normalizes SAST findings from Bandit & Semgrep into unified SARIF schemas.
- **Intraprocedural AST Slicing & Context**: Slices vulnerable code paths from sink to source and enriches context using CWE knowledge bases.
- **Constrained LLM Patch Generation**: Generates minimal unified diffs with structured JSON schemas and abstention support (`cannot_fix`).
- **Deterministic Static Patch Guard**: Blocks out-of-scope modifications, banned dangerous calls (`eval`, `exec`), disallowed imports, and cosmetic suppression comments (`# nosec`).
- **Multi-Stage Validation Pipeline**: Runs baseline test checks, patched tests, security regression tests, and automated re-scans.
- **Cryptographic Server Approval Gate**: Guarantees that code branches and pull requests can never be created without explicit reviewer approval.
- **Rich CLI for Viva & Demonstrations**: Built-in Typer CLI with interactive walkthrough mode (`patchpilot demo`).

---

## Directory Structure

```text
patchpilot/
├── backend/            # FastAPI REST & WebSocket API, Celery worker, domain modules
│   └── src/patchpilot/
│       ├── api/        # REST route handlers & error mappers
│       ├── core/       # Security, state machine, audit log, events
│       ├── db/         # SQLAlchemy 2.0 models & session management
│       ├── context/    # AST analysis, backward slicing, token budget
│       ├── scanning/   # SARIF parser, fingerprinting, Bandit/Semgrep adapters
│       ├── llm/        # LLM Gateway, providers (Fake/Ollama/OpenAI), prompts
│       ├── repair/     # Patch generator, static guard, repair loop
│       └── validation/ # Staged validation, verdict engine, workspace manager
├── shared/
│   └── pp_contracts/   # Shared schemas and HMAC request signing
├── benchmarks/         # Seed applications and evaluation benchmarks
├── data/artifacts/     # Ephemeral logs, test reports, and diff artifacts
└── tests/              # Unit, integration, and sandbox abuse suites
```

---

## Getting Started

### 1. Prerequisites
- Python 3.11+ (Windows, Linux, or macOS)
- Git

### 2. Environment Setup
```bash
# Create and activate virtual environment
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# Linux / macOS
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -e shared/pp_contracts
pip install -e backend
```

### 3. Run Unit Tests
```bash
python -m pytest tests/unit -v
```

### 4. CLI Demonstration
```bash
# System status & health check
patchpilot health

# Run security scan on target directory
patchpilot scan benchmarks/seed_projects/clean_shop

# Run interactive walkthrough for teachers / viva
patchpilot demo --cwe CWE-89
```

