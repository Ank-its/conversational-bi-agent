import logging

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool

from app.config import AppConfig
from app.prompts import AGENT_SYSTEM_PROMPT
from app.services.database import DatabaseService

logger = logging.getLogger(__name__)


class AgentService:
    """Wraps LangGraph SQL agent. Handles LLM interaction and query execution."""

    def __init__(self, config: AppConfig, db_service: DatabaseService):
        self._config = config
        self._db_service = db_service
        self._agent = self._create_agent()

    def _create_agent(self):
        """Create a ReAct SQL agent with DuckDB tools."""
        db_service = self._db_service

        @tool
        def run_sql(query: str) -> str:
            """Execute a SQL query against the Instacart DuckDB database and return results.
            Use this to run SELECT queries. Always include LIMIT for large tables.
            The database uses DuckDB SQL syntax (similar to PostgreSQL)."""
            try:
                result = db_service.execute(query)
                if result.empty:
                    return "Query returned no results."
                return result.to_string(index=False, max_rows=30)
            except Exception as e:
                return f"SQL Error: {e}. Please fix the query and try again."

        @tool
        def list_tables() -> str:
            """List all tables in the database with their row counts."""
            con = db_service.get_connection()
            tables = con.execute("SHOW TABLES").fetchall()
            result = []
            for t in tables:
                count = con.execute(f"SELECT COUNT(*) FROM {t[0]}").fetchone()[0]
                cols = con.execute(
                    f"SELECT column_name FROM information_schema.columns WHERE table_name = '{t[0]}'"
                ).fetchall()
                col_names = ", ".join(c[0] for c in cols)
                result.append(f"  {t[0]} ({count:,} rows): {col_names}")
            con.close()
            return "Tables:\n" + "\n".join(result)

        @tool
        def describe_table(table_name: str) -> str:
            """Get column names, types, and 3 sample rows for a specific table."""
            try:
                con = db_service.get_connection()
                cols = con.execute(f"DESCRIBE {table_name}").fetchdf()
                sample = con.execute(f"SELECT * FROM {table_name} LIMIT 3").fetchdf()
                con.close()
                return f"Schema:\n{cols.to_string(index=False)}\n\nSample rows:\n{sample.to_string(index=False)}"
            except Exception as e:
                return f"Error: {e}"

        llm = ChatOpenAI(
            model=self._config.openai_model,
            temperature=0,
            api_key=self._config.openai_api_key,
        )
        return create_react_agent(llm, [run_sql, list_tables, describe_table], prompt=AGENT_SYSTEM_PROMPT)

    def _build_prompt(self, query: str, history: list[tuple[str, str]] | None = None) -> str:
        """Build the full prompt with conversation context."""
        context = ""
        if history:
            recent = history[-3:]
            context = "Previous conversation:\n"
            for q, a in recent:
                context += f"Q: {q}\nA: {a[:300]}\n"
            context += "\n"
        return f"""{context}User question: {query}

Answer the question by querying the database. Return the result clearly formatted."""

    async def stream_execute_query(self, query: str, history: list[tuple[str, str]] | None = None):
        """Stream agent execution, yielding (message_chunk, metadata) tuples."""
        full_prompt = self._build_prompt(query, history)
        async for event in self._agent.astream(
            {"messages": [("human", full_prompt)]},
            stream_mode="messages",
        ):
            msg_chunk, metadata = event
            yield msg_chunk, metadata
