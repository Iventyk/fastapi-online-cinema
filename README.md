![coverage](https://img.shields.io/badge/coverage-0%25-red)

# FastAPI Online Cinema

This is the backend API for the FastAPI Online Cinema project.

## Getting Started

Follow these steps to set up your development environment and run the project.

### 1. Clone the repository

```bash
git clone https://github.com/Iventyk/fastapi-online-cinema.git
cd fastapi-online-cinema
```

### 2. Install dependencies with Poetry

Make sure you have Poetry installed.

```poetry install```

This will create a virtual environment automatically and install all required dependencies.

### 3. Run the FastAPI server

```poetry run uvicorn src.main:app --reload```

The server will run on http://127.0.0.1:8000 by default.
Use --reload to enable auto-reload on code changes.






## Git Workflow

This document describes a **safe and predictable Git workflow** for a team project where:

- `main` — stable branch (production / releases)
- `develop` — main development branch
- each task is implemented in a **separate feature branch**

The goal is to **minimize merge conflicts**, avoid losing changes, and keep the commit history clean and readable.

---

### 0. General Rules

- ❌ **NEVER push directly to** `develop` **or** `main`
- ✅ All work must be done via **feature branches** (each developer creates their own branch)
- ✅ Before any `pull`, `merge`, or `rebase`, the working tree **must be clean** (no uncommitted changes)
- ✅ All changes are merged into the repository **only via Pull Requests**

