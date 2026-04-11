# WhatsApp CRM — Chatbot Engine

A production-ready Django REST Framework backend for building and running WhatsApp chatbots. Powered by Django 5.1, PostgreSQL, Redis, and Celery with full WhatsApp Cloud API integration including native WhatsApp Flows.

---

## Getting Started

### Prerequisites

- Docker & Docker Compose
- A Meta Business account with WhatsApp Cloud API access (for production)

### 1. Clone & configure

```bash
git clone <repository-url> whatsapp-crm
cd whatsapp-crm
cp .env.example .env
```

Edit `.env` and set at minimum:

```
DJANGO_SECRET_KEY=<generate-a-long-random-string>
```

For WhatsApp integration, fill in the `WHATSAPP_*` variables from your Meta Business dashboard.

### 2. Start all services

```bash
docker compose up --build -d
```

This starts **5 services**: PostgreSQL, Redis, Django web server, Celery worker, and Celery beat.

### 3. Run migrations

```bash
docker compose exec web python manage.py migrate
```

### 4. Create a superuser

```bash
docker compose exec web python manage.py createsuperuser
```

### 5. Verify

| Check | Command / URL |
|-------|---------------|
| Health | `curl http://localhost:8000/health/` |
| Admin | http://localhost:8000/admin/ |
| Swagger | http://localhost:8000/api/schema/swagger-ui/ |
| Container status | `docker compose ps` |
| Celery tasks | `docker compose logs celery-worker` |

### Stopping

```bash
docker compose down          # stop containers
docker compose down -v       # stop + delete volumes (wipes DB)
```

---

## Makefile Commands

All commands run inside Docker containers — no local Python install needed. Run `make help` for a quick reference.

### Docker

```bash
make up               # Start all services in background
make down             # Stop all services
make build            # Build/rebuild containers
make restart          # Restart all services
make logs             # Tail all container logs
make logs-web         # Tail web container logs only
make bash             # Open a bash shell in the web container
```

### Django

```bash
make migrate          # Run database migrations
make makemigrations   # Generate new migration files
make superuser        # Create a Django superuser
make check            # Run Django system checks
make collectstatic    # Collect static files
make showurls         # List all registered URL patterns
make shell            # Open Django shell
make dbshell          # Open PostgreSQL shell
```

### Code Quality

```bash
make lint             # Run ruff linter (check only, no changes)
make lint-fix         # Run ruff linter and auto-fix issues
make format           # Format all code with ruff
make format-check     # Check formatting without making changes
make pylint           # Run pylint on apps/, core/, infrastructure/
make typecheck        # Run mypy type checker
```

**Shortcut commands:**

```bash
make qa               # Run ALL quality checks (lint + format-check + typecheck + Django check)
make fix              # Auto-fix everything (lint-fix + format)
```

Typical workflow:

```bash
# Before committing
make fix              # auto-fix lint + format
make qa               # verify everything passes

# Or in CI
make qa               # fails on any issue
```

### Testing

```bash
make test             # Run test suite with pytest
make test-cov         # Run tests with coverage report
```

### Celery

```bash
make celery-worker    # Start celery worker (foreground)
make celery-beat      # Start celery beat (foreground)
make celery-logs      # Tail celery worker + beat logs
```

### Database

```bash
make flush            # Flush all data (keep tables)
make reset-db         # Drop & recreate database + run migrations
make reset-migrations # Delete all migration files and regenerate from scratch
```

### Cleanup

```bash
make clean            # Remove __pycache__, .pyc, .pyo files
```

---

## Architecture Overview

```
                        ┌──────────────────────────────┐
                        │       Meta Cloud API         │
                        └──────┬───────────────┬───────┘
                     webhook POST          send message
                               │                  ▲
                               ▼                  │
┌─────────────────────────────────────────────────────────────────┐
│  apps/integrations                                              │
│  ┌─────────────────┐   signature    ┌────────────────────────┐  │
│  │ webhook (verify) │──  check  ──▶ │  _handle_incoming_msg  │  │
│  └─────────────────┘                └──────────┬─────────────┘  │
│                                        nfm_reply│  text/button   │
│                                     ┌───────────┘               │
│                                     ▼                           │
│                          ┌─────────────────────┐                │
│                          │  whatsapp_flow.py   │                │
│                          │  (flow responses)   │                │
│                          └─────────────────────┘                │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  apps/conversation                                              │
│  ┌──────────────────┐    ┌────────────┐    ┌─────────────────┐  │
│  │ ConversationEngine│───▶│ renderers  │    │    actions       │  │
│  │  (engine.py)      │    │ render_node│    │ trigger_flow    │  │
│  └────────┬─────────┘    └────────────┘    │ send_template   │  │
│           │                                │ api_call        │  │
│           ▼                                └─────────────────┘  │
│  ┌─────────────────┐                                            │
│  │ services.py      │ persist_conversation → Conversation model │
│  └─────────────────┘                                            │
└─────────────────────────────────────────────────────────────────┘
        │ session R/W                          │ Celery tasks
        ▼                                      ▼
┌───────────────┐                    ┌──────────────────┐
│ Redis         │                    │ apps/messaging   │
│ SessionStore  │                    │ send_message_task│
│ (24h TTL)     │                    │ send_template    │
└───────────────┘                    │ external_api_call│
                                     └────────┬─────────┘
                                              │
                                              ▼
                                     ┌──────────────────┐
                                     │ infrastructure/  │
                                     │ WhatsAppClient   │
                                     │ (httpx → Meta)   │
                                     └──────────────────┘
```

---

## Project Structure

```
whatsapp-crm/
├── core/                    # Django project config
│   ├── settings/
│   │   ├── base.py          # Shared settings (DB, Redis, DRF, Celery, JWT)
│   │   ├── dev.py           # Debug toolbar, no throttling
│   │   └── prod.py          # HSTS, SSL, secure cookies
│   ├── celery.py
│   ├── urls.py              # Root URL conf with versioned API
│   ├── wsgi.py / asgi.py
│
├── apps/
│   ├── accounts/            # Business management
│   ├── chatbot_builder/     # Chatbot graph (nodes, options)
│   ├── conversation/        # Runtime engine, session management
│   ├── integrations/        # WhatsApp webhook + flow handler
│   ├── messaging/           # Outgoing messages + Celery tasks
│   └── common/              # Abstract models, exceptions, permissions
│
├── infrastructure/
│   ├── redis.py             # SessionStore (django-redis)
│   └── whatsapp_client.py   # WhatsApp Cloud API client (httpx)
│
├── docker-compose.yml       # Postgres + Redis + Web + Worker + Beat
├── Dockerfile
├── requirements.txt
└── .env.example
```

---

## App Documentation

### `apps/common` — Shared Utilities

Provides abstract base classes and DRF utilities used across all apps.

**Abstract Models:**

| Model | Purpose |
|-------|---------|
| `TimeStampedModel` | `created_at` (indexed), `updated_at`; default ordering `-created_at` |
| `UUIDModel` | UUID primary key — hides sequential IDs from API |

**DRF Utilities:**

| Module | Class / Function | Purpose |
|--------|-----------------|---------|
| `exceptions.py` | `custom_exception_handler` | Uniform error responses with `status_code` field |
| `permissions.py` | `IsOwnerOrReadOnly` | Write access restricted to object owner |
| `permissions.py` | `IsBusinessMember` | Ensures user owns the referenced business |
| `pagination.py` | `StandardPagination` | Page size 25, max 100, `page_size` param |

---

### `apps/accounts` — Business Management

Manages business entities that own chatbots and receive WhatsApp messages.

**Model: `Business`**

| Field | Type | Notes |
|-------|------|-------|
| `name` | CharField(255) | Business display name |
| `whatsapp_phone_number_id` | CharField(50) | Meta phone number ID (unique) |
| `whatsapp_number` | CharField(20) | Display number (unique) |
| `owner` | FK → User | Business owner |
| `is_active` | Boolean | Default `True` |

**API Endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/accounts/businesses/` | List user's businesses |
| POST | `/api/v1/accounts/businesses/` | Create a business |
| GET | `/api/v1/accounts/businesses/{id}/` | Retrieve |
| PUT/PATCH | `/api/v1/accounts/businesses/{id}/` | Update |
| DELETE | `/api/v1/accounts/businesses/{id}/` | Delete |

All endpoints require JWT authentication. Queryset scoped to `owner=request.user`.

---

### `apps/chatbot_builder` — Chatbot Graph Configuration

Design chatbot conversation flows as a directed graph of nodes and options stored in PostgreSQL.

**Models:**

| Model | Key Fields | Notes |
|-------|-----------|-------|
| `Chatbot` | `business`, `name`, `is_active`, `enable_back`, `enable_restart` | UniqueConstraint: 1 active chatbot per business |
| `Node` | `chatbot`, `type`, `content` (JSON), `is_start` | Types: `menu`, `text`, `template`, `flow`, `action`, `end`. UniqueConstraint: 1 start node per chatbot |
| `Option` | `node`, `type`, `label`, `value`, `next_node`, `action` (JSON), `order` | Types: `text`, `button`, `list`, `checkbox` |

**API Endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| GET/POST | `/api/v1/chatbot/chatbots/` | List / create chatbots |
| GET/PUT/PATCH/DELETE | `/api/v1/chatbot/chatbots/{id}/` | Retrieve with nested nodes |
| GET/POST | `/api/v1/chatbot/nodes/` | List / create nodes |
| GET/PUT/PATCH/DELETE | `/api/v1/chatbot/nodes/{id}/` | CRUD |
| GET/POST | `/api/v1/chatbot/options/` | List / create options |
| GET/PUT/PATCH/DELETE | `/api/v1/chatbot/options/{id}/` | CRUD |

List view uses a lightweight `ChatbotListSerializer` (no nested nodes). Detail view includes full node tree with options.

**Option action payload examples:**

```json
// Send a WhatsApp template
{"type": "send_template", "template_name": "order_confirmation"}

// Trigger a WhatsApp Flow
{
  "type": "trigger_flow",
  "flow_type": "whatsapp",
  "flow_id": "123456789",
  "return_node_id": 20,
  "body_text": "Place your order",
  "flow_cta": "Order Now"
}

// Call an external API
{"type": "api_call", "url": "https://api.example.com/orders", "method": "POST"}
```

---

### `apps/conversation` — Runtime Engine

The core conversation engine that processes incoming messages against the chatbot graph, with session state in Redis.

**Model: `Conversation`**

| Field | Type | Notes |
|-------|------|-------|
| `business` | FK → Business | |
| `user_phone` | CharField(50) | Indexed |
| `data` | JSONField | All collected data from the session |
| `completed_at` | DateTimeField | Auto-set on creation |

**API Endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/conversations/` | List completed conversations |
| GET | `/api/v1/conversations/{id}/` | Retrieve conversation detail |

Read-only. Scoped to businesses owned by the authenticated user.

**Engine (`ConversationEngine.process`):**

1. No session → create one, render start node
2. Active flow → respond with "please complete the form"
3. System commands: `0` = back, `#` = restart
4. Resolve option by `value` match → collect data → execute action
5. If action triggers a flow → save session with `active_flow`, pause (return `None`)
6. If next node is `end` → persist conversation, delete session
7. Otherwise → advance to next node, render it

**Redis Session Structure:**

```json
{
  "current_node_id": 12,
  "history": [1, 5],
  "collected_data": {"3": "pizza", "5": "large"},
  "active_flow": {
    "type": "whatsapp",
    "flow_id": "123456789",
    "return_node_id": 20
  }
}
```

**Key Modules:**

| Module | Function | Purpose |
|--------|----------|---------|
| `engine.py` | `ConversationEngine.process()` | Main message processing loop |
| `renderers.py` | `render_node(node)` | Convert Node → WhatsApp payload (text, menu, template, flow) |
| `actions.py` | `execute_action(action, phone, session)` | Dispatch actions (template, API call, trigger flow) |
| `services.py` | `persist_conversation()` | Save completed session data to DB |

---

### `apps/messaging` — Outbound Messages & Celery Tasks

Tracks all outgoing messages and handles async delivery via Celery.

**Model: `OutgoingMessage`**

| Field | Type | Notes |
|-------|------|-------|
| `phone` | CharField(50) | Recipient, indexed |
| `content` | JSONField | Message payload |
| `status` | CharField | `pending` / `sent` / `failed` |
| `retry_count` | PositiveSmallInt | |
| `provider_message_id` | CharField | Meta message ID |
| `error_detail` | TextField | Last error |

**API Endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/messaging/messages/` | List messages (filterable by `status`, `phone`) |
| GET | `/api/v1/messaging/messages/{id}/` | Retrieve message detail |

**Celery Tasks:**

| Task | Max Retries | Purpose |
|------|-------------|---------|
| `send_message_task` | 5 | Send text, template, or flow message. Routes to appropriate `WhatsAppClient` method |
| `send_template_task` | 5 | Send a specific template |
| `external_api_call_task` | 3 | POST/GET to external API with exponential backoff |

All tasks use `acks_late=True` for reliability. Retries use exponential backoff (`2^attempt` seconds). 4xx errors are treated as fatal (no retry), 5xx as transient.

---

### `apps/integrations` — WhatsApp Webhook

Handles inbound communication from Meta's WhatsApp Cloud API.

**Endpoint:**

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/integrations/whatsapp/webhook/` | Meta subscription verification |
| POST | `/api/v1/integrations/whatsapp/webhook/` | Receive incoming messages |

Both are public (`AllowAny`) with `WebhookThrottle` (500/min).

**Webhook POST processing:**

1. Verify HMAC-SHA256 signature (`X-Hub-Signature-256` header vs `WHATSAPP_APP_SECRET`)
2. Iterate `entry[].changes[].value.messages[]`
3. Resolve `Business` by `metadata.phone_number_id`
4. Route by message type:
   - `text` → conversation engine
   - `interactive.button_reply` / `list_reply` → conversation engine
   - `interactive.nfm_reply` → WhatsApp Flow response handler

**WhatsApp Flow Response (`whatsapp_flow.py`):**

When a user completes a WhatsApp Flow, Meta sends an `nfm_reply`. The handler:

1. Loads session from Redis
2. Validates `flow_id` matches `session.active_flow.flow_id`
3. Merges flow response data into `session.collected_data`
4. Clears `active_flow`
5. Jumps to `return_node_id` (or stays on current node)
6. Renders and sends the next node

---

### `infrastructure/` — External Services

**`redis.py` — SessionStore:**

| Method | Purpose |
|--------|---------|
| `get(business_id, phone)` | Load session from Redis |
| `save(business_id, phone, session)` | Save with 24h TTL |
| `delete(business_id, phone)` | Clear session |

Key format: `session:{business_id}:{phone}`. Uses `django-redis` cache backend for connection pooling.

**`whatsapp_client.py` — WhatsAppClient:**

| Method | Purpose |
|--------|---------|
| `send_text(phone, text)` | Plain text message |
| `send_template(phone, template_name, language)` | Template message |
| `send_flow(phone, flow_id, ...)` | WhatsApp Flow (native rich UI) |
| `send_interactive_buttons(phone, body, buttons)` | Up to 3 reply buttons |
| `send_interactive_list(phone, body, button, sections)` | List picker |

All methods use `httpx` with 10s timeout. Errors are logged and re-raised for Celery retry handling.

---

## API Reference

All API endpoints (except webhook and health) require JWT authentication.

### Authentication

Obtain tokens via SimpleJWT (add routes as needed):

```
POST /api/v1/auth/token/          → { access, refresh }
POST /api/v1/auth/token/refresh/  → { access }
```

Access token lifetime: **30 minutes**. Refresh: **7 days** (rotated).

### Global Settings

| Setting | Value |
|---------|-------|
| Pagination | 25 items/page, max 100 |
| Throttle (anon) | 100/hour |
| Throttle (user) | 1000/hour |
| Throttle (webhook) | 500/minute |
| Filtering | django-filter + search + ordering |

### OpenAPI Schema

- JSON: `GET /api/schema/`
- Swagger UI: `GET /api/schema/swagger-ui/`

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DJANGO_SECRET_KEY` | Yes | — | Django secret key |
| `DJANGO_SETTINGS_MODULE` | No | `core.settings.dev` | Settings module |
| `DJANGO_ALLOWED_HOSTS` | No | `""` | Comma-separated hosts |
| `POSTGRES_DB` | No | `whatsapp_crm` | Database name |
| `POSTGRES_USER` | No | `postgres` | DB user |
| `POSTGRES_PASSWORD` | No | `postgres` | DB password |
| `POSTGRES_HOST` | No | `localhost` | DB host |
| `POSTGRES_PORT` | No | `5432` | DB port |
| `REDIS_URL` | No | `redis://localhost:6379/0` | Redis URL for cache |
| `CELERY_BROKER_URL` | No | `REDIS_URL` | Celery broker |
| `CELERY_RESULT_BACKEND` | No | `REDIS_URL` | Celery results |
| `WHATSAPP_API_URL` | No | `https://graph.facebook.com/v21.0` | Meta API base URL |
| `WHATSAPP_API_TOKEN` | Yes* | — | Bearer token for Cloud API |
| `WHATSAPP_VERIFY_TOKEN` | Yes* | — | Webhook subscription verify token |
| `WHATSAPP_APP_SECRET` | Yes* | — | HMAC signature verification |
| `WHATSAPP_PHONE_NUMBER_ID` | Yes* | — | Phone number ID for sending |
| `CORS_ALLOWED_ORIGINS` | No | — | Comma-separated origins (prod) |

*Required for WhatsApp integration to function.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | Django 5.1 + Django REST Framework |
| Database | PostgreSQL 16 |
| Cache & Sessions | Redis 7 + django-redis |
| Task Queue | Celery 5.4 with Redis broker |
| HTTP Client | httpx |
| Auth | SimpleJWT (access + refresh tokens) |
| API Docs | drf-spectacular (OpenAPI 3.0 + Swagger UI) |
| Containerization | Docker + Docker Compose |
| Production Server | Gunicorn / Uvicorn (ASGI) |
