# Instacart Conversational BI Agent

A production-grade conversational Business Intelligence agent that converts natural language questions into SQL queries against the Instacart grocery dataset (38M+ rows).

## Architecture

```
┌──────────────────┐        HTTP/JSON        ┌──────────────────────────┐
│   Next.js UI     │  ───────────────────►    │                          │
│   (Frontend)     │   POST /api/chat        │   FastAPI Backend        │
│   :3000          │   GET  /api/health      │                          │
│                  │  ◄───────────────────   │   :8000                  │
└──────────────────┘    ChatResponse          │                          │
                                             │  ┌─────────────────────┐ │
                                             │  │ QueryRefinerService │ │
                                             │  │ PlannerService      │ │
                                             │  │ AgentService        │──── LangGraph ReAct
                                             │  │ ChartService        │     + GPT-4o-mini
                                             │  │ DatabaseService     │──── DuckDB
                                             │  │ SessionManager      │
                                             │  └─────────────────────┘ │
                                             └──────────────────────────┘
```

## Tech Stack

| Component | Technology | Justification |
|-----------|-----------|---------------|
| Backend API | FastAPI | Async-ready, auto OpenAPI docs, Pydantic validation |
| Frontend | Next.js 15 + TypeScript | App Router, TanStack Query, Tailwind CSS |
| LLM Framework | LangGraph + LangChain | ReAct agent pattern with tool-calling |
| LLM | GPT-4o-mini | Cost-effective, fast, strong SQL reasoning |
| Database | DuckDB | Columnar analytics DB, handles 32M rows in-process |
| Validation | Pydantic | Request/response type safety, serialization |
| Containerization | Docker Compose | Reproducible multi-service deployment |

## Project Structure

```
├── backend/                   # FastAPI backend service
│   ├── app/
│   │   ├── main.py            # App entrypoint & lifespan
│   │   ├── config.py          # Pydantic settings
│   │   ├── exceptions.py      # Custom exception handlers
│   │   ├── models/            # Request/response schemas
│   │   ├── services/          # Business logic layer
│   │   ├── routers/           # API route handlers
│   │   └── schema/            # DB schema context for LLM
│   ├── Dockerfile
│   └── requirements.txt
├── frontend-next/             # Next.js frontend (primary)
│   ├── src/
│   │   ├── app/               # Next.js App Router (layout, page, globals)
│   │   ├── components/        # UI components (sidebar, chat)
│   │   ├── hooks/             # React hooks (new-chat, health)
│   │   ├── lib/               # Types, API client, utils, constants
│   │   └── providers/         # QueryClient + Chat context providers
│   ├── Dockerfile
│   └── package.json
├── frontend-streamlit/        # Streamlit frontend (archived)
├── data/                      # Instacart CSV files (git-ignored)
├── docs/                      # Project documentation
├── docker-compose.yml
└── README.md
```

## Setup

### Prerequisites
- Docker & Docker Compose
- OpenAI API key
- Instacart CSV data files in `data/`

### Quick Start (Docker)

```bash
# 1. Configure environment variables
cp backend/.env.example backend/.env
# Edit backend/.env — set your OPENAI_API_KEY

# 2. Place CSV files in data/
#    orders.csv, order_products__prior.csv, order_products__train.csv,
#    products.csv, aisles.csv, departments.csv

# 3. Start services
docker compose up --build

# Next.js Frontend: http://localhost:3000
# Backend API:      http://localhost:8000
# API Docs:         http://localhost:8000/docs
```

### Running Individual Frontends

```bash
# Next.js frontend (recommended)
docker compose up backend frontend-next

# Streamlit frontend (legacy)
docker compose up backend frontend
```

### Manual Setup

```bash
# Backend
cd backend
cp .env.example .env
# Edit .env with your OPENAI_API_KEY
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Next.js Frontend (separate terminal)
cd frontend-next
npm install
npm run dev
# Opens at http://localhost:3000
```

### Environment Variables

**Backend** (`backend/.env`):

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | *(required)* | OpenAI API key |
| `OPENAI_MODEL` | `gpt-4o-mini` | LLM model to use |
| `DB_PATH` | `instacart.db` | DuckDB database file path |
| `DATA_DIR` | `data` | Directory containing CSV data |
| `LOG_LEVEL` | `INFO` | Logging level |
| `MAX_RETRIES` | `2` | Max agent execution retries |
| `CHART_DPI` | `100` | Chart image resolution |
| `MAX_RESULT_ROWS` | `30` | Max rows in query results |

**Frontend** (`frontend-next/.env.local`):

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend API base URL |

## API Documentation

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/chat` | Send a query, get response with table/chart |
| `POST` | `/api/chat/new` | Create a new chat session |
| `GET` | `/api/chat/{session_id}` | Get chat history |
| `GET` | `/api/health` | Health check with DB stats |
| `GET` | `/api/schema` | Database schema information |

### Request/Response Examples

**POST /api/chat**
```json
// Request
{
  "query": "What are the top 10 most ordered products?",
  "session_id": "uuid-here"
}

// Response
{
  "answer": "Here are the top 10 most ordered products...",
  "plan": "1. Join order_products_prior with products...",
  "table_data": [{"product_name": "Banana", "order_count": 472254}],
  "chart": {
    "chart_type": "bar",
    "image_base64": "iVBOR...",
    "filename": "top_10_most_ordered_products.png"
  },
  "session_id": "uuid-here",
  "refined_query": null
}
```

## Data Model

```
departments (21 rows)          aisles (134 rows)
    │                              │
    └── department_id ◄── products ──► aisle_id ──┘
                          (50K rows)
                              │
                          product_id
                              │
              ┌───────────────┼───────────────┐
              ▼                               ▼
   order_products_prior          order_products_train
       (32M rows)                    (1.4M rows)
              │                               │
          order_id                        order_id
              │                               │
              └───────────────┬───────────────┘
                              ▼
                           orders
                         (3.4M rows)
```

## Key Design Decisions

1. **Frontend/Backend Separation**: Next.js frontend acts as a thin client, all logic in FastAPI. Enables independent scaling and testing.
2. **React Context over Zustand**: Chat state is small (few sessions), no need for external state library.
3. **TanStack Query**: Handles API caching, retries, and loading states for the frontend.
4. **Dependency Injection**: Backend services instantiated once at startup and injected via `app.state`.
5. **Base64 Charts**: Charts returned as base64 PNGs in API responses, eliminating filesystem dependencies.
6. **In-Memory Sessions**: Chat sessions stored in memory for simplicity.
7. **Multi-stage Docker**: Smaller runtime images by separating build dependencies.

## Known Limitations

- Chat sessions are in-memory (lost on backend restart)
- No authentication/authorization on API endpoints
- Single DuckDB connection per query (no connection pooling)
- Chart generation is synchronous (blocks the request)
- No rate limiting on API endpoints
