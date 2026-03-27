from fastapi import APIRouter, Request

from app.models.responses import HealthResponse, SchemaResponse, TableInfo
from app.schema.metadata import TABLE_METADATA

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check(request: Request):
    """Return database health status."""
    db_service = request.app.state.db_service
    info = db_service.health_check()
    return HealthResponse(
        status=info["status"],
        database=info["database"],
        tables=info["tables"],
        total_rows=info["total_rows"],
    )


@router.get("/schema", response_model=SchemaResponse)
def get_schema(request: Request):
    """Return database schema information."""
    db_service = request.app.state.db_service
    tables = []
    try:
        con = db_service.get_connection()
        for table_name, meta in TABLE_METADATA.items():
            count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            tables.append(TableInfo(
                name=table_name,
                row_count=count,
                columns=list(meta["columns"].keys()),
                description=meta["description"],
            ))
        con.close()
    except Exception:
        pass
    return SchemaResponse(tables=tables)
