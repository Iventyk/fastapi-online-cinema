# FastAPI Online Cinema

An Online Cinema is a digital platform that allows users to select, watch, and purchase access to movies and other video materials via the internet. 

This is the backend API for the FastAPI Online Cinema project.

### Tech Stack & Tools

![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.128.0-009688?logo=fastapi&logoColor=white)
![Uvicorn](https://img.shields.io/badge/Uvicorn-0.40.0-4DB33D?logo=python&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0.46-52B0E7?logo=sqlalchemy&logoColor=white)
![Alembic](https://img.shields.io/badge/Alembic-1.18.3-000000?logo=python&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-2.12.5-1C83C6?logo=python&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-5.6.2-FF6600?logo=celery&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7.1.0-DC382D?logo=redis&logoColor=white)
![Stripe](https://img.shields.io/badge/Stripe-14.3.0-635BFF?logo=stripe&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-latest-2496ED?logo=docker&logoColor=white)
![Docker Compose](https://img.shields.io/badge/Docker%20Compose-latest-2496ED?logo=docker&logoColor=white)
![Poetry](https://img.shields.io/badge/Poetry-latest-000000?logo=python&logoColor=white)

![Pytest](https://img.shields.io/badge/Pytest-9.0.2-0A74DA?logo=pytest&logoColor=white)
![Pytest-Asyncio](https://img.shields.io/badge/Pytest--Asyncio-1.3.0-0A74DA?logo=pytest&logoColor=white)
![Black](https://img.shields.io/badge/Black-26.1.0-000000?logo=python&logoColor=white)
![Flake8](https://img.shields.io/badge/Flake8-7.3.0-000000?logo=python&logoColor=white)
![Mypy](https://img.shields.io/badge/Mypy-1.19.1-000000?logo=python&logoColor=white)

![Swagger](https://img.shields.io/badge/OpenAPI%203-latest-000000?logo=openapiinitiative&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-latest-2088FF?logo=githubactions&logoColor=white)

### Test Coverage

[![codecov](https://codecov.io/github/Iventyk/fastapi-online-cinema/graph/badge.svg?token=XU2A2361K3)](https://codecov.io/github/Iventyk/fastapi-online-cinema)


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

# Core Dependencies
```
imports:

from src.schemas import CurrentUser
from src.security import JWTAuthManagerInterface, get_current_user
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
```
DB Schema - https://dbdiagram.io/d/Accounts-app-675ef6bee763df1f00fd8ed1
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


## Payments

### Overview
The payment system allows users to pay for orders using Stripe and receive email notifications about their payment status. It also supports admin views and webhook handling for transaction validation.

---

### User Functionality
- Users can create a payment for an order.
- After successful payment:
  - The order status is updated to `PAID`.
  - The user receives an email confirmation.
- Users can view a history of all their payments, including:
  - Date and time of payment
  - Amount
  - Status (`pending`, `successful`, `canceled`, `refunded`)
  - Itemized details of each order

#### API Endpoints
- `POST /payments/{order_id}` — Create payment for a specific order. Returns `client_secret` for Stripe.
- `GET /payments/` — Get all payments of the authenticated user.

---

### Admin Functionality
- Admins can view all payments with optional filters:
  - By user ID
  - By status (`successful`, `canceled`, `refunded`)
- Only users with `ADMIN` permission can access admin endpoints.

#### API Endpoints
- `GET /payments/admin` — Get all payments (admin only) with filters.

---

### Payment Processing
- Uses Stripe as the payment gateway.
- Validates:
  - Total amount of the order
  - Order status (`PENDING`)
  - User authentication
- Creates `Payment` and `PaymentItem` records in the database.
- Triggers **Celery tasks** to send payment notification emails:
  - `send_payment_success_email_task` — sent after successful payment
  - `send_payment_failed_email_task` — sent if payment fails

---

### Webhooks
- `POST /webhooks/stripe` — Receives Stripe events to validate payments and update order/payment statuses.
- Updates Payment and Order status automatically based on webhook event type.
- Sends email notifications for successful or failed payments via Celery tasks.

---

### Database Models
- **Payment**
  - `id: int`
  - `user_id: int` — foreign key to users
  - `order_id: int` — foreign key to orders
  - `amount: Decimal`
  - `status: PaymentStatusEnum` (`SUCCESSFUL`, `CANCELED`, `REFUNDED`)
  - `external_payment_id: str | None`
  - `created_at: datetime`
- **PaymentItem**
  - `id: int`
  - `payment_id: int` — foreign key to Payment
  - `order_item_id: int` — foreign key to OrderItem
  - `price_at_payment: Decimal`

- DB Schema https://dbdiagram.io/d/Payment-app-675f1a65e763df1f00ff70c6

---

### Email Notifications
- **Payment Success**
  - Triggered after payment is successfully processed.
  - Includes order details and amount.
- **Payment Failed**
  - Triggered if payment fails or is declined.
  - Provides instructions to the user to retry or select a different payment method.

All email sending is handled asynchronously via Celery tasks, ensuring non-blocking behavior during API calls.

---

## Orders Module Overview

**Order Status Lifecycle** – Tracks the state of a transaction from creation to finalization.
```
PENDING – payment is in progress
PAID – movie is already purchased (cannot be added to cart again)
CANCELED – transaction failed
```

**Orders Models:**

**Order** - Represents a collection of movies a user intends to purchase.
```
Fields:
id – primary key
user_id – foreign key to users
status – enum (PENDING, PAID, CANCELED)
total_amount – total price (Decimal)
created_at – timestamp

Relationships:
One-to-many with OrderItemModel (Order.items)
Many-to-one with UserModel (Order.user)
```

**OrderItem** - A snapshot of a movie within a specific order.
```
Fields:
id – primary key
order_id – foreign key to orders
movie_id – foreign key to movies
price_at_order – the price of the movie at the time the order was created (Decimal)

Notes:
Ensures historical financial accuracy even if movie prices change later.
```

**Validation & Business Logic** - Ensures data integrity and security.

```
1. Smart Creation (Filtering):
   - Excludes movies already purchased (PAID).
   - Excludes movies already in another PENDING order.
   - Filters out unavailable (deleted or region-locked) movies.
   - Function: create_order(...) -> returns list of 'removed_items'.

2. Integrity Checks:
   - Prevents creating an order from an empty cart.
   - Ensures users can only access their own orders.

3. Price Revalidation:
   - Re-scans current movie prices before payment finalization.
   - Updates 'total_amount' and 'price_at_order' if database prices changed.
   - Function: revalidate_order_prices(order_id)

4. Order Cancellation:
   - Users can cancel PENDING orders before payment.
   - PAID orders require a refund request (direct cancellation blocked).
```

**API Endpoints:**

**User Functionality:**
- `POST /orders/` — Create a new order from cart (with auto-filtering).
- `GET /orders/` — Get all orders of the authenticated user.
- `PATCH /orders/{order_id}/cancel` — Cancel a specific pending order.

**Admin/Moderator Functionality:**
- `GET /orders/admin` — Get all system orders with filters:
   - By User ID
   - By Status (pending, paid, canceled)
   - By Date Range
## Stripe Payment Integration

This section explains how to set up and test Stripe payments for the application.

### 1. Stripe Account Setup
1. Register or log in to your [Stripe Dashboard](https://dashboard.stripe.com/).
2. Create an API key and a webhook secret for your environment.
3. Add them to your `.env` or environment variables:

`STRIPE_API_KEY=your_stripe_api_key`
`STRIPE_WEBHOOK_SECRET=your_stripe_webhook_secret`

### 2. Install Stripe CLI
If you haven't installed it yet, follow instructions here: [Stripe CLI](https://docs.stripe.com/stripe-cli).

### 3. Login to Stripe CLI
Run:

`stripe login`

Follow the browser authentication flow.

### 4. Listen for Webhooks
Forward Stripe events to your local API:

`stripe listen --forward-to localhost:8000/webhooks/stripe`

This allows your local application to receive Stripe webhook events in real time.

### 5. Test Payments
Create a payment intent and confirm it using the Stripe CLI:

`stripe payment_intents confirm <PAYMENT_INTENT_ID> --payment-method pm_card_visa`

Replace `<PAYMENT_INTENT_ID>` with the actual payment intent ID from your Stripe dashboard.

### 6. Notes
- Payment success/failure emails are sent automatically via Celery tasks.
- Ensure MailHog (or your SMTP server) is running to view test emails.
- Use pm_card_visa for testing successful payments, and other test payment methods for simulating different scenarios.

---
