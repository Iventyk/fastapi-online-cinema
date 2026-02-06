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


## Run with Docker

### 1. Create `.env`

Create `.env` from `.env.sample`.

Windows (PowerShell):
```Copy-Item .env.sample .env```

Linux/macOS/WSL/Git Bash:
```cp .env.sample .env```

### 2. Build and start services

```docker compose up -d --build```

### 3. Apply migrations (run manually)

Migrations are not executed automatically on `up`. Run them explicitly:

```docker compose --profile migrate run --rm migrator```

### Local URLs

API docs:
http://127.0.0.1:8000/docs

MailHog UI:
http://127.0.0.1:8025

MinIO Console:
http://127.0.0.1:9001


### Stop services

```docker compose down```
