import duckdb
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(BASE_DIR, "instacart.db")


def setup_database():
    """Load all 6 CSVs into DuckDB with proper table names."""
    con = duckdb.connect(DB_PATH)

    tables = {
        "orders": "orders.csv",
        "order_products_prior": "order_products__prior.csv",
        "order_products_train": "order_products__train.csv",
        "products": "products.csv",
        "aisles": "aisles.csv",
        "departments": "departments.csv",
    }

    for table_name, csv_file in tables.items():
        csv_path = os.path.join(DATA_DIR, csv_file).replace("\\", "/")
        existing = con.execute(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?",
            [table_name],
        ).fetchone()[0]
        if existing == 0:
            con.execute(
                f"CREATE TABLE {table_name} AS SELECT * FROM read_csv_auto('{csv_path}')"
            )
            print(f"  Loaded {table_name} from {csv_file}")
        else:
            print(f"  Table {table_name} already exists, skipping")

    con.close()
    print("Database setup complete:", DB_PATH)
    return DB_PATH


if __name__ == "__main__":
    setup_database()
