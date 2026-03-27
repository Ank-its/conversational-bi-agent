import logging
import os

import duckdb
import pandas as pd

from app.config import AppConfig
from app.exceptions import DatabaseError

logger = logging.getLogger(__name__)


class DatabaseService:
    """Manages DuckDB connection lifecycle. Singleton per application."""

    def __init__(self, config: AppConfig):
        self._config = config
        self._db_path = config.db_path
        self._data_dir = config.data_dir

    def setup(self) -> None:
        """Load all CSVs into DuckDB if tables don't exist."""
        tables = {
            "orders": "orders.csv",
            "order_products_prior": "order_products__prior.csv",
            "order_products_train": "order_products__train.csv",
            "products": "products.csv",
            "aisles": "aisles.csv",
            "departments": "departments.csv",
        }

        try:
            con = duckdb.connect(self._db_path)
            for table_name, csv_file in tables.items():
                csv_path = os.path.join(self._data_dir, csv_file).replace("\\", "/")
                existing = con.execute(
                    "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?",
                    [table_name],
                ).fetchone()[0]
                if existing == 0:
                    con.execute(
                        f"CREATE TABLE {table_name} AS SELECT * FROM read_csv_auto('{csv_path}')"
                    )
                    logger.info("Loaded %s from %s", table_name, csv_file)
                else:
                    logger.debug("Table %s already exists, skipping", table_name)
            con.close()
            logger.info("Database setup complete: %s", self._db_path)
        except Exception as e:
            raise DatabaseError(f"Failed to setup database: {e}") from e

    def get_connection(self) -> duckdb.DuckDBPyConnection:
        """Get a read-only connection to the database."""
        try:
            return duckdb.connect(self._db_path, read_only=True)
        except Exception as e:
            raise DatabaseError(f"Failed to connect to database: {e}") from e

    def execute(self, query: str) -> pd.DataFrame:
        """Execute a SQL query and return results as DataFrame."""
        try:
            con = self.get_connection()
            result = con.execute(query).fetchdf()
            con.close()
            return result
        except Exception as e:
            raise DatabaseError(f"Query execution failed: {e}") from e

    def health_check(self) -> dict:
        """Return database health info: status, table count, total rows."""
        try:
            con = self.get_connection()
            tables = con.execute("SHOW TABLES").fetchall()
            total_rows = 0
            for t in tables:
                count = con.execute(f"SELECT COUNT(*) FROM {t[0]}").fetchone()[0]
                total_rows += count
            con.close()
            return {
                "status": "healthy",
                "database": self._db_path,
                "tables": len(tables),
                "total_rows": total_rows,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "database": self._db_path,
                "tables": 0,
                "total_rows": 0,
                "error": str(e),
            }
