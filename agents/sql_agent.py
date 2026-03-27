import os
import duckdb
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "instacart.db")

SYSTEM_PROMPT = """You are a SQL expert working with a DuckDB database containing Instacart grocery data.

DATABASE SCHEMA:
- orders (order_id, user_id, eval_set, order_number, order_dow, order_hour_of_day, days_since_prior_order)
  ~3.4M rows. days_since_prior_order is NULL for first orders.
- order_products_prior (order_id, product_id, add_to_cart_order, reordered)
  ~32M rows. Historical orders (all but the last order per user). ALWAYS use aggregation, never SELECT *.
- order_products_train (order_id, product_id, add_to_cart_order, reordered)
  ~1.4M rows. Each user's LAST/most recent order (131K users). Same schema as prior, zero overlap.
- products (product_id, product_name, aisle_id, department_id)
  ~50K rows. Product catalog.
- aisles (aisle_id, aisle)
  134 rows. Product subcategories.
- departments (department_id, department)
  21 rows. Top-level product categories.

KEY RELATIONSHIPS:
- order_products_prior.order_id -> orders.order_id
- order_products_train.order_id -> orders.order_id
- order_products_prior.product_id -> products.product_id
- order_products_train.product_id -> products.product_id
- products.aisle_id -> aisles.aisle_id
- products.department_id -> departments.department_id

DATA SPLIT (important):
- order_products_prior + order_products_train have ZERO overlap. Together they form the complete purchase history.
- For comprehensive BI analysis, use UNION ALL:
  SELECT * FROM order_products_prior UNION ALL SELECT * FROM order_products_train
- If the user asks about "all orders" or "all products ordered", combine both tables.
- If the user specifically asks about historical/prior data only, use order_products_prior alone.
- The orders table also has eval_set='test' (75K orders) with NO product data available.

RULES:
1. ALWAYS use LIMIT (default 20) for large result sets
2. For order_products_prior (32M rows), ALWAYS aggregate - never full table scan
3. days_since_prior_order is NULL for first orders (order_number=1)
4. reordered=1 means user bought this product before, 0 means first time
5. order_dow: 0=Saturday through 6=Friday
6. Use DuckDB SQL syntax
7. Format results as readable tables
8. When asked about products with departments/aisles, JOIN through the products table
9. For reorder rate, calculate: SUM(reordered) * 100.0 / COUNT(*) as reorder_rate"""


def _get_connection():
    return duckdb.connect(DB_PATH, read_only=True)


@tool
def run_sql(query: str) -> str:
    """Execute a SQL query against the Instacart DuckDB database and return results.
    Use this to run SELECT queries. Always include LIMIT for large tables.
    The database uses DuckDB SQL syntax (similar to PostgreSQL)."""
    try:
        con = _get_connection()
        result = con.execute(query).fetchdf()
        con.close()
        if result.empty:
            return "Query returned no results."
        return result.to_string(index=False, max_rows=30)
    except Exception as e:
        return f"SQL Error: {e}. Please fix the query and try again."


@tool
def list_tables() -> str:
    """List all tables in the database with their row counts."""
    con = _get_connection()
    tables = con.execute("SHOW TABLES").fetchall()
    result = []
    for t in tables:
        count = con.execute(f"SELECT COUNT(*) FROM {t[0]}").fetchone()[0]
        cols = con.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{t[0]}'").fetchall()
        col_names = ", ".join(c[0] for c in cols)
        result.append(f"  {t[0]} ({count:,} rows): {col_names}")
    con.close()
    return "Tables:\n" + "\n".join(result)


@tool
def describe_table(table_name: str) -> str:
    """Get column names, types, and 3 sample rows for a specific table."""
    try:
        con = _get_connection()
        cols = con.execute(f"DESCRIBE {table_name}").fetchdf()
        sample = con.execute(f"SELECT * FROM {table_name} LIMIT 3").fetchdf()
        con.close()
        return f"Schema:\n{cols.to_string(index=False)}\n\nSample rows:\n{sample.to_string(index=False)}"
    except Exception as e:
        return f"Error: {e}"


def create_agent():
    """Create a ReAct SQL agent with DuckDB tools."""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    tools = [run_sql, list_tables, describe_table]

    agent = create_react_agent(
        llm,
        tools,
        prompt=SYSTEM_PROMPT,
    )

    return agent
