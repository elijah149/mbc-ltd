# MBCU LTD Management System — Backend

Production-ready ERP backend built with **FastAPI + PostgreSQL + Redis + Celery + MinIO**,
matching the organizational hierarchy:

```
Board of Directors (Body Manager)
        -> Manager
            -> Production Manager -> Weighing Officer, Industry Employee
            -> Store Keeper
            -> Accountant Manager -> Accountant Officer -> Accounts Clerk
            -> Operation Manager -> Operation Officer
            -> IT Officer
```

## 1. Muundo wa Mradi (Project Structure)

```
backend/
  app/
    api/            # Route handlers (one file per module)
    core/            # config, database, security, storage, celery, rate-limit
    models/         # SQLAlchemy ORM models
    schemas/        # Pydantic request/response schemas
    main.py          # FastAPI app entrypoint
    seed.py          # seeds departments, roles, permissions, hierarchy, admin user
  alembic/          # database migrations
  requirements.txt
  Dockerfile
  docker-compose.yml
  .env.example
```

## 2. Kuendesha kwa Docker (Recommended)

```bash
cp .env.example .env
docker compose up --build
```

Hii itaanzisha: PostgreSQL, Redis, MinIO, backend (FastAPI), na Celery worker.
Migrations na seed data (roles/departments/permissions/admin user) zitaendeshwa moja kwa moja.

- API docs (Swagger): http://localhost:8000/docs
- API docs (ReDoc): http://localhost:8000/redoc
- MinIO console: http://localhost:9001

**Admin wa kwanza (default):**
- Email: `admin@mbcu.co.tz`
- Password: `ChangeMe123!`
(Badilisha hii mara moja baada ya login ya kwanza, au badilisha kwenye `.env` kabla ya kuanzisha.)

## 3. Kuendesha Bila Docker (Local Dev)

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# hakikisha POSTGRES_SERVER=localhost na Redis/MinIO ziko locally, au badilisha .env

alembic revision --autogenerate -m "initial schema"
alembic upgrade head
python -m app.seed

uvicorn app.main:app --reload
```

## 4. Authentication Flow

```
POST /api/v1/auth/login     -> { access_token, refresh_token }
POST /api/v1/auth/refresh   -> { access_token }
POST /api/v1/auth/logout    -> requires Bearer access_token
GET  /api/v1/auth/me        -> current user profile
```

Tumia `Authorization: Bearer <access_token>` kwenye kila request nyingine.

## 5. Ramani Kamili ya Endpoints (API Integration Guide)

| Module | Method & Path | Notes |
|---|---|---|
| Auth | `POST /auth/login`, `/auth/logout`, `/auth/refresh`, `GET /auth/me` | JWT access + refresh |
| Users | `GET/POST /users`, `GET/PUT/DELETE /users/{id}` | requires `manage_users` / `create_staff` / `delete_staff` |
| Roles | `GET/POST /roles`, `GET /permissions` | RBAC configuration |
| Departments | `GET/POST /departments` | |
| Staff | `GET/POST /staff`, `PUT/DELETE /staff/{id}` | |
| Production | `GET /production`, `GET/POST /production/batches`, `POST /production/batches/{id}/approve`, `POST /weighing`, `GET/POST /production/logs` | role-gated: Weighing Officer, Production Manager, Manager |
| Inventory | `GET /inventory`, `GET/POST /inventory/items`, `POST /stock-in`, `POST /stock-out` | auto-notifies Manager on low stock |
| Finance | `GET/POST /expenses`, `GET/POST /revenues`, `GET/POST /payments`, `POST /approve-payment/{id}` | multi-level approval chain, see below |
| Operations | `GET/POST /operations`, `PUT/DELETE /operations/{id}` | Operation Manager / Officer |
| Documents | `GET/POST /documents`, `GET /documents/{id}/download-url` | multipart upload, stored in MinIO |
| Notifications | `GET /notifications`, `POST /notifications/{id}/read` | per-user |
| Audit Logs | `GET /audit-logs` | requires `view_reports` |
| Dashboard | `GET /dashboard/stats`, `/dashboard/finance`, `/dashboard/production`, `/dashboard/inventory` | |

All paths are prefixed with `/api/v1`.

## 6. Approval Workflows

**Financial** (`POST /api/v1/approve-payment/{payment_id}` with `{"approve": true|false}`):
```
Accounts Clerk -> Accountant Officer -> Accountant Manager -> Manager -> Approved
```
Only the user whose role matches the *next* required stage can advance the payment.
Each step is fully audit-logged and notifies the payment's creator.

**Production**:
```
Industry Employee -> Weighing Officer -> Production Manager -> Manager
```
Weighing officers record `POST /weighing`; Production Managers/Managers finalize via
`POST /production/batches/{id}/approve`.

**Inventory**:
```
Store Keeper -> Manager
```
Store Keeper manages stock directly; Manager is auto-notified when any item drops
below its `minimum_stock` threshold.

## 7. RBAC Model

- `permissions` table: atomic capabilities (`create_staff`, `manage_finance`, etc.)
- `roles` table: named roles with a `level` (hierarchy depth) and `reports_to_role_id`
- `role_permissions`: many-to-many linking roles to permissions
- Two guard styles are available in `app/api/deps.py`:
  - `require_permission("manage_inventory")` — capability-based (preferred for most endpoints)
  - `require_role("Manager", "Board Director")` — identity-based (used for workflow gates)

Run `python -m app.seed` any time to (re-)apply the default role/permission/hierarchy setup
defined in `app/seed.py` — it's idempotent, safe to re-run.

## 8. Audit Logging

Every create/update/approve/delete action across all modules calls
`app.core.audit.log_action(...)`, writing to `audit_logs` with old/new value snapshots.
View via `GET /api/v1/audit-logs?table_name=payments&user_id=3`.

## 9. Testing

```bash
pytest
```
A starter test suite is in `tests/` (see `tests/test_auth.py`) — extend per module
following the same pattern (spin up a TestClient, seed roles, hit endpoints).

## 10. Kuunganisha na Frontend Yako (Connecting Your Frontend)

1. Weka `BACKEND_CORS_ORIGINS` kwenye `.env` liwe na domain/URL ya frontend yako.
2. Frontend inapaswa kuhifadhi `access_token` na `refresh_token` (kwa mfano secure storage/cookie).
3. Tumia interceptor ya HTTP client (Axios/Dio/Fetch) kuongeza `Authorization: Bearer <token>`
   kwenye kila request, na kuita `/auth/refresh` pale access token inapoisha muda (401).
4. Swagger UI (`/docs`) inaonyesha schema kamili ya kila request/response — tumia kama
   "contract" wakati wa kuunganisha forms/tables za frontend yako zilizopo.
