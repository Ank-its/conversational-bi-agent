# Instacart Conversational BI Agent

A production-grade conversational Business Intelligence agent that converts natural language questions into SQL queries against the Instacart grocery dataset (38M+ rows). Features real-time streaming of query plans and agent reasoning via Server-Sent Events (SSE).

## Architecture

```
┌──────────────────┐     SSE Stream          ┌──────────────────────────┐
│   Next.js UI     │  ───────────────────►   │                          │
│   (Frontend)     │  POST /api/chat/stream  │   FastAPI Backend        │
│   :3000          │  GET  /api/health       │                          │
│                  │  ◄───────────────────   │   :8000                  │
└──────────────────┘   plan → agent → result │                          │
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
| Frontend | Next.js 15 + TypeScript | App Router, Tailwind CSS, React Context |
| LLM Framework | LangGraph + LangChain | ReAct agent pattern with tool-calling |
| LLM | GPT-4o-mini | Cost-effective, fast, strong SQL reasoning |
| Database | DuckDB | Columnar analytics DB, handles 32M rows in-process |
| Streaming | SSE (Server-Sent Events) | Real-time plan + agent token streaming |
| Markdown | react-markdown + remark-gfm | GFM tables, lists, code blocks in chat |
| Containerization | Docker Compose | Reproducible multi-service deployment |

## Dataset

This project uses the **Instacart Online Grocery Basket Analysis** dataset from Kaggle.

> **Download:** [kaggle.com/datasets/yasserh/instacart-online-grocery-basket-analysis-dataset](https://www.kaggle.com/datasets/yasserh/instacart-online-grocery-basket-analysis-dataset)

### How to get the data

1. Go to the Kaggle dataset page linked above
2. Click **Download** and export the data as **CSV files**
3. Place the following 6 CSV files in the `data/` folder at the project root:

```
data/
├── aisles.csv
├── departments.csv
├── order_products__prior.csv
├── order_products__train.csv
├── orders.csv
└── products.csv
```

> **Important:** The `data/` folder is git-ignored. You must download and place the CSV files manually before running the application.

## Project Structure

```
├── backend/                   # FastAPI backend service
│   ├── app/
│   │   ├── main.py            # App entrypoint & lifespan
│   │   ├── config.py          # Pydantic settings
│   │   ├── exceptions.py      # Custom exception handlers
│   │   ├── models/            # Request/response schemas
│   │   ├── prompts/           # LLM prompt templates
│   │   ├── services/          # Business logic layer
│   │   ├── routers/           # API route handlers
│   │   └── schema/            # DB schema context for LLM
│   ├── Dockerfile
│   └── requirements.txt
├── frontend-next/             # Next.js frontend
│   ├── src/
│   │   ├── app/               # Next.js App Router (layout, page, globals)
│   │   ├── components/        # UI components (sidebar, chat)
│   │   ├── hooks/             # React hooks (new-chat, health)
│   │   ├── lib/               # Types, API client, utils, constants
│   │   └── providers/         # Chat context + streaming state
│   ├── Dockerfile
│   └── package.json
├── data/                      # Instacart CSV files (git-ignored)
├── docker-compose.yml
└── README.md
```

## Setup

### Prerequisites
- Docker & Docker Compose
- OpenAI API key
- Instacart CSV data files in `data/` (see [Dataset](#dataset) section above)

### Quick Start (Docker)

```bash
# 1. Configure environment variables
cp backend/.env.example backend/.env
# Edit backend/.env — set your OPENAI_API_KEY

# 2. Download CSV files from Kaggle and place them in data/
#    (see Dataset section above for download link and file list)

# 3. Start services
docker compose up --build

# Frontend:  http://localhost:3000
# Backend:   http://localhost:8000
# API Docs:  http://localhost:8000/docs
```

### Manual Setup

```bash
# Backend
cd backend
cp .env.example .env
# Edit .env with your OPENAI_API_KEY
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Frontend (separate terminal)
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
| `POST` | `/api/chat/stream` | Stream query plan + agent execution via SSE |
| `POST` | `/api/chat/new` | Create a new chat session |
| `GET` | `/api/chat/{session_id}` | Get chat history |
| `GET` | `/api/health` | Health check with DB stats |
| `GET` | `/api/schema` | Database schema information |

### SSE Stream Format

**POST /api/chat/stream**
```json
// Request
{
  "query": "What are the top 10 most ordered products?",
  "session_id": "uuid-here"
}
```

The response is a stream of Server-Sent Events:
```
data: {"type":"plan","chunk":"1. Join order_products"}     // plan tokens
data: {"type":"plan","chunk":"_prior with products..."}
data: {"type":"plan_done","plan":"full plan text"}          // plan complete
data: {"type":"tool_call","name":"run_sql","args":"..."}    // tool invocation
data: {"type":"tool_result","result":"..."}                 // tool output
data: {"type":"agent","chunk":"Here are the top"}           // answer tokens
data: {"type":"agent","chunk":" 10 most ordered..."}
data: {"type":"result","data":{...ChatResponse...}}         // final result with table + chart
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

1. **Real-Time SSE Streaming**: Plan generation and agent reasoning stream token-by-token to the frontend, replacing static loading spinners with live progress.
2. **Frontend/Backend Separation**: Next.js frontend acts as a thin client, all logic in FastAPI. Enables independent scaling and testing.
3. **React Context for Chat + Streaming**: Chat state and streaming phases managed via React Context — no external state library needed.
4. **GFM Markdown Rendering**: Streaming and final responses render through `react-markdown` with `remark-gfm` for proper table, list, and code block formatting.
5. **Dependency Injection**: Backend services instantiated once at startup and injected via `app.state`.
6. **Base64 Charts**: Charts returned as base64 PNGs in API responses, eliminating filesystem dependencies.
7. **In-Memory Sessions**: Chat sessions stored in memory for simplicity.
8. **Multi-stage Docker**: Smaller runtime images by separating build dependencies.

## Known Limitations

- Chat sessions are in-memory (lost on backend restart)
- No authentication/authorization on API endpoints
- Single DuckDB connection per query (no connection pooling)
- No rate limiting on API endpoints
