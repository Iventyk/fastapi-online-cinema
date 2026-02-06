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


# Core Dependencies
```
imports:

from src.schemas import CurrentUser
from src.securuty import JWTAuthManagerInterface, get_current_user
from src.config import get_jwt_manager, get_settings, Settings
from src.databases import get_db

Realizations:

Annotated[Settings, Depends(get_settings)] - retrieve settings object;

db: Annotated[AsyncSession, Depends(get_db)] - retrieve db session;

jwt_manager: Annotated[JWTAuthManagerInterface, Depends(get_jwt_manager)] - retrieve jwt_manager

current_user: Annotated[CurrentUser, Depends(get_current_user)] - retrieve current authorized user

```




