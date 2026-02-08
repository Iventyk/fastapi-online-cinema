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

## Shopping Cart Module Overview
**StatusEnum** - Defines the lifecycle of an order. Used in the Shopping Cart module to validate purchase history before adding items (preventing duplicate purchases).
```
PENDING – payment is in progress
PAID – movie is already purchased (cannot be added to cart again)
CANCELED – transaction failed
```
**Shopping Cart Models:**

**Cart** - Represents a user's storage for movies.
```
Fields:
id – primary key
user_id – unique foreign key to users

Relationships:
One-to-one with UserModel (Cart.user)
One-to-many with CartItemModel (Cart.items)

Notes:
Automatically created for the user if it doesn't exist during item addition.
Strictly one cart per user.
```
**CartItem** - Represents a specific movie added to a cart.
```
Fields:
id – primary key
cart_id – foreign key to carts
movie_id – foreign key to movies

Relationships:
Many-to-one with CartModel
Many-to-one with MovieModel

Notes:
Acts as a link between the user's cart and the movie catalog.
Includes validation to prevent duplicate items in the same cart.
```
**Validation** - The module enforces strict rules to ensure data integrity and security.
```
1. User Validation:
   - Ensures the user exists before any operation.
   - Function: validate_user(user_id)

2. Role-Based Access Control (RBAC):
   - Users can only access/modify their own carts.
   - Moderators and Admins have elevated permissions to view/clear/extend any user's cart.
   - Function: validate_user_permission(...)

3. Movie Availability:
   - Checks if the requested movie exists in the database.
   - Function: validate_movie(movie_id)

4. Cross-Module Purchase Validation (Relation to Orders):
   - Before adding a movie to the cart, the system checks the Order history.
   - Prevents adding a movie if it is already in a PAID or PENDING order.
   - Function: validate_movie_purchase_status(...)
```

**Business Logic && Cart Services**

Function - `sync_guest_cart_to_user` - Handles the transition of shopping cart data from a guest session (local storage/cookies) to the persistent database when a user logs in or registers.

Trigger Points:
```
- Successful Registration
- Successful Login
```
Workflow:
```
1. Validation: Checks if any movie IDs were passed from the guest session.
2. Cart Retrieval: Fetches the user's persistent cart from the database.
   - Auto-creation: If the user has no cart, a new one is created immediately.
3. Smart Merge (Deduplication):
   - Identifies movies already present in the user's database cart.
   - Calculates the difference: `Movies to Add = Guest IDs - Existing DB IDs`.
   - Prevents duplicate entries for the same movie.
4. Persistence: Bulk inserts the new items into the `cart_items` table and commits the transaction.

Goal: ensures a seamless user experience where items added before authentication are not lost.
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
