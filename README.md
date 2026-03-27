# Instacart Conversational BI Agent

A production-grade conversational Business Intelligence agent that converts natural language questions into SQL queries against the Instacart grocery dataset (38M+ rows).

## Architecture

```
┌──────────────────┐        HTTP/JSON        ┌──────────────────────────┐
│                  │  ───────────────────►    │                          │
│   Streamlit UI   │   POST /api/chat        │   FastAPI Backend        │
│   (Frontend)     │   GET  /api/health      │                          │
│   :8501          │  ◄───────────────────   │   :8000                  │
│                  │    ChatResponse          │                          │
└──────────────────┘                         │  ┌─────────────────────┐ │
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
| Frontend | Streamlit | Rapid prototyping, built-in chat UI, dataframe rendering |
| LLM Framework | LangGraph + LangChain | ReAct agent pattern with tool-calling |
| LLM | GPT-4o-mini | Cost-effective, fast, strong SQL reasoning |
| Database | DuckDB | Columnar analytics DB, handles 32M rows in-process |
| Validation | Pydantic | Request/response type safety, serialization |
| Containerization | Docker Compose | Reproducible multi-service deployment |

## Project Structure

```
Hireathon-1/
├── backend/                 # FastAPI backend service
│   ├── app/
│   │   ├── main.py          # App entrypoint & lifespan
│   │   ├── config.py         # Pydantic settings
│   │   ├── exceptions.py     # Custom exception handlers
│   │   ├── models/           # Request/response schemas
│   │   ├── services/         # Business logic layer
│   │   ├── routers/          # API route handlers
│   │   └── schema/           # DB schema context for LLM
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env                  # Backend environment variables (git-ignored)
│   └── .env.example          # Backend env template
├── frontend/                # Streamlit frontend service
│   ├── app.py               # Chat UI
│   ├── api_client.py        # Backend HTTP client
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env                 # Frontend environment variables (git-ignored)
│   └── .env.example         # Frontend env template
├── data/                    # Instacart CSV files (git-ignored)
├── docs/                    # Project documentation
│   ├── EVALUATION_SCORECARD.md
│   ├── test_queries.md
│   └── test_results/
├── docker-compose.yml
├── .gitignore
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

cp frontend/.env.example frontend/.env
# Frontend defaults are fine (BACKEND_URL=http://backend:8000)

# 2. Place CSV files in data/
#    orders.csv, order_products__prior.csv, order_products__train.csv,
#    products.csv, aisles.csv, departments.csv

# 3. Start both services
docker-compose up --build

# Frontend: http://localhost:8501
# Backend:  http://localhost:8000
# API Docs: http://localhost:8000/docs
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
cd frontend
cp .env.example .env
pip install -r requirements.txt
streamlit run app.py
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

**Frontend** (`frontend/.env`):

| Variable | Default | Description |
|----------|---------|-------------|
| `BACKEND_URL` | `http://backend:8000` | Backend API base URL |

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

The dataset captures Instacart's grocery ordering history across 6 tables:

- **orders** (3.4M rows) — Each row is a single order placed by a user, with metadata like day of week, hour of day, and days since the user's previous order.
- **order_products_prior** (32M rows) — The main fact table. Each row links an order to a product, representing one item in a user's basket. Contains the `add_to_cart_order` (sequence the item was added) and whether it was a `reordered` item.
- **order_products_train** (1.4M rows) — Same structure as prior, but holds the most recent order per user (used as the training set in the original Kaggle competition).
- **products** (50K rows) — Product catalog with name, linked to an aisle and department.
- **aisles** (134 rows) — Aisle names (e.g., "fresh fruits", "yogurt").
- **departments** (21 rows) — Department names (e.g., "produce", "dairy eggs").

The `products` table is the central dimension: it connects to `departments` and `aisles` for categorization, and to the two order-product tables via `product_id`. The order-product tables join to `orders` via `order_id`, completing the chain from "who ordered when" to "what product in which category."

## Key Design Decisions

1. **Frontend/Backend Separation**: Streamlit acts as a thin client, all logic in FastAPI. Enables independent scaling and testing.
2. **Per-Service Environment**: Each service has its own `.env` file, keeping secrets isolated to the services that need them.
3. **Dependency Injection**: Services are instantiated once at startup and injected via `app.state`. No global singletons.
4. **Base64 Charts**: Charts are returned as base64-encoded PNGs in the API response, eliminating filesystem dependencies.
5. **In-Memory Sessions**: Chat sessions stored in memory for simplicity. Trade-off: sessions lost on restart.
6. **Pydantic Validation**: All API inputs validated with field constraints (e.g., query length 1-1000 chars).
7. **Multi-stage Docker**: Smaller runtime images by separating build dependencies.

## Known Limitations

- Chat sessions are in-memory (lost on backend restart)
- No authentication/authorization on API endpoints
- Single DuckDB connection per query (no connection pooling)
- Chart generation is synchronous (blocks the request)
- No rate limiting on API endpoints
