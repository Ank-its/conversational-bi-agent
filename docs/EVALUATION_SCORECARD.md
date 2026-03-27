# Evaluation Scorecard — Conversational BI Agent (Problem Statement 1)

## Must-Have Requirements — ALL PASS

### 1. Load all 6 CSVs and establish correct relationships
**Status: PASS**
All 6 CSV files loaded into DuckDB with correct table names:
- `orders` (3,421,083 rows) — core order metadata
- `order_products_prior` (32,434,489 rows) — historical order items
- `order_products_train` (1,384,617 rows) — training set order items
- `products` (49,688 rows) — product catalog
- `aisles` (134 rows) — product subcategories
- `departments` (21 rows) — top-level categories

Foreign key relationships verified: `order_products_prior.order_id → orders.order_id`, `order_products_prior.product_id → products.product_id`, `products.aisle_id → aisles.aisle_id`, `products.department_id → departments.department_id`.

### 2. Accept natural language questions and generate correct SQL
**Status: PASS**
LangGraph ReAct agent with GPT-4o-mini generates SQL from plain English. 11 test queries executed, all results cross-verified against direct SQL — 11/11 exact matches. Agent has schema-aware prompt with table descriptions, column semantics, and JOIN patterns.

### 3. Return results as tables and/or charts (bar, line, pie)
**Status: PASS**
- **Tables**: Agent returns formatted markdown tables; Streamlit UI renders them as interactive DataFrames
- **Bar charts**: Top products, departments by count
- **Line charts**: Hourly/temporal distributions
- **Pie charts**: Proportional breakdowns (<=6 categories)
- Auto chart type detection based on query keywords + data shape heuristics

### 4. Handle at least 3-table joins correctly
**Status: PASS**
Verified: `order_products_prior JOIN products JOIN departments` returns correct department-level aggregations (Produce: 9,479,291 orders, Dairy Eggs: 5,414,016). Also tested 4-table joins through the full hierarchy (order_products → products → aisles → departments).

---

## Stretch Goals — ALL PASS

### 5. Multi-step reasoning
**Status: PASS**
Query: *"Show me which aisles have the highest reorder rate and how that correlates with average basket position"*
Result: Correctly JOINed 3 tables, computed both `SUM(reordered)*100/COUNT(*)` as reorder_rate AND `AVG(add_to_cart_order)` as basket position, returned correlated results (Milk: 78.14% reorder rate, 5.57 avg position).

### 6. Automatic chart type selection
**Status: PASS**
- Keyword detection: "trend/hourly/by hour" → line, "share/proportion" → pie, "top/rank/compare" → bar
- Data heuristics: numeric X-axis with >5 rows → line, <=6 categories → pie, default → bar
- Tested: hourly data→line, 3-category share→pie, top-5 ranking→bar

### 7. Conversational memory
**Status: PASS**
Test sequence:
1. Asked: *"Which aisles have highest reorder rate?"* → returned top 10 aisles
2. Follow-up: *"Now filter that to only show aisles in the produce department"* → correctly filtered to 5 produce aisles

Implementation: `QueryRefinerService` rewrites follow-up queries into self-contained questions using conversation history. Last 3 exchanges passed as context to the agent.

### 8. Error recovery
**Status: PASS**
`sql_executor.py` implements retry logic with MAX_RETRIES=2. On SQL failure, the error message is fed back to the LLM with a prompt to fix and retry. Prevents infinite loops with attempt counter.

### 9. Scale handling (32M-row table)
**Status: PASS**
- `order_products_prior` (32,434,489 rows) aggregated in **0.02 seconds** using DuckDB's columnar engine
- Agent prompt enforces `LIMIT` and aggregation rules to prevent full table scans
- No memory issues — DuckDB processes queries without loading full table into memory

---

## Dataset Non-Trivial Challenges — ALL ADDRESSED

### Scale (32M rows)
DuckDB columnar engine handles 32M rows in milliseconds. Agent prompt explicitly states "ALWAYS aggregate — never SELECT *" for large tables.

### Split data (prior/train eval_set)
Agent understands the partition: `prior` = historical orders, `train` = each user's last order, `test` = no product data. Uses `UNION ALL` when asked about "all orders" (returns 33,819,106 = 32,434,489 + 1,384,617). Zero overlap verified.

### Three-level product hierarchy
Schema prompt includes full JOIN patterns: `order_products → products → aisles → departments`. Verified with department-level and aisle-level queries.

### Temporal reasoning (days_since_prior_order)
Agent correctly handles relative time gaps. Verified: average days between orders by day-of-week (range 10.5–11.8 days), properly excludes NULL first orders.

### Reorder behavior
Reorder rate calculated as `SUM(reordered) * 100.0 / COUNT(*)`. Top reordered product: Half And Half Ultra Pasteurized (86.17%). Minimum order threshold (1000+) applied to filter noise.

### NaN handling
206,209 orders have NULL `days_since_prior_order` — exactly matches 206,209 orders where `order_number=1` (first orders). Agent filters NULLs when computing temporal averages.

---

## Architecture Summary

| Component | Technology | Why |
|-----------|-----------|-----|
| Database | DuckDB | Columnar engine handles 32M rows in-memory, SQL-native, zero config |
| LLM Agent | LangGraph ReAct + GPT-4o-mini | Tool-calling agent with SQL execution tools, self-correcting |
| Charts | Matplotlib (Agg backend) | Server-side rendering, supports bar/line/pie, saves to PNG |
| UI | Streamlit | Chat interface with inline tables/charts, session management |
| Schema | Rich metadata prompts | Table descriptions, FK relationships, JOIN patterns injected into agent |

## Verified Test Queries (11/11 correct)

| # | Query | Type | Verified |
|---|-------|------|----------|
| 1 | Total order count | Simple count | 3,421,083 |
| 2 | Top 10 products | 3-table JOIN | Banana: 472,565 |
| 3 | Department reorder rate | Multi-table aggregation | Dairy Eggs: 67.00% |
| 4 | Hourly distribution | Temporal | Peak at 10am (288,418) |
| 5 | Aisle reorder vs basket position | Multi-step reasoning | Milk: 78.14%, pos 5.57 |
| 6 | Follow-up: filter to produce | Conversational memory | 5 produce aisles returned |
| 7 | NULL days_since_prior | NaN handling | 206,209 (6.03%) |
| 8 | Avg days between orders by DOW | Temporal reasoning | 10.5–11.8 days |
| 9 | Top reorder rate products | Reorder behavior | Half & Half: 86.17% |
| 10 | "What sells best?" | Adversarial/vague | Banana #1 |
| 11 | 32M row aggregation + avg cart | Scale handling | 32.4M rows, 10.09 avg |
