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

Annotated[Settings, Depends(get_settings)] 
- retrieve settings object;

db: Annotated[AsyncSession, Depends(get_db)] 
- retrieve db session;

jwt_manager: Annotated[JWTAuthManagerInterface, Depends(get_jwt_manager)] 
- retrieve jwt_manager

current_user: Annotated[CurrentUser, Depends(get_current_user)] 
- retrieve current authorized user

```


##  Authorization and Authentication Overview
**UserGroupEnum** - Defines user access levels within the system:
```
USER – default application user
MODERATOR – elevated permissions
ADMIN – full administrative access
```

**GenderEnum** - Used in user profiles:
```
MALE
FEMALE
```
**User Groups**
```
UserGroupModel
Represents a role/group assigned to users.

Fields:
id – primary key
name – unique group name (UserGroupEnum)

Relationships:
One-to-many with UserModel (UserGroupModel.users)

Notes:
Each user belongs to at most one group
Groups are used for authorization and role-based access control (RBAC)
```
**UserModel**
```
UserModel
Represents an application user and authentication identity.

Fields:
id – primary key
email – unique email address (indexed)
hashed_password – securely stored password hash
is_active – account activation status
created_at – creation timestamp
updated_at – last update timestamp
group_id – foreign key to user_groups

Relationships:
Many-to-one with UserGroupModel
One-to-one with UserProfileModel
One-to-one with ActivationTokenModel
One-to-one with PasswordResetTokenModel
One-to-many with RefreshTokenModel

Security Design:
Passwords are write-only
Password hashing and validation are enforced at the model level
Raw passwords are never stored or exposed

Utility Methods:
create(...) – factory method for safe user creation
check_password(...) – verifies password against stored hash
has_group(...) – role membership check
```
**UserProfileModel**
```
UserProfileModel
Stores optional personal and demographic information for a user.

Fields:
id – primary key
first_name
last_name
avatar – URL or path to profile image
gender – GenderEnum
date_of_birth
info – free-form additional information
user_id – unique foreign key to users

Relationships:
One-to-one with UserModel

Notes:
Profile is optional but strictly one profile per user
Automatically deleted when the user is deleted
```
**Token System**
```
All tokens inherit from a shared abstract base.
TokenBaseModel (Abstract)
Base model for all user-related tokens.

Common Fields:
id – primary key
token – unique token string
expires_at – expiration datetime (UTC)
user_id – foreign key to users

Notes:
Tokens are time-limited
Cascade deletion ensures cleanup when a user is removed
```

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
