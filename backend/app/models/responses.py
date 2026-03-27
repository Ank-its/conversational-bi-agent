from pydantic import BaseModel, Field


class ChartData(BaseModel):
    chart_type: str = Field(..., description="Chart type: bar, line, or pie")
    image_base64: str = Field(..., description="PNG image encoded as base64")
    filename: str = Field(..., description="Original filename of the chart")


class ChatResponse(BaseModel):
    answer: str
    plan: str
    table_data: list[dict] | None = None
    chart: ChartData | None = None
    session_id: str
    refined_query: str | None = None


class HealthResponse(BaseModel):
    status: str
    database: str
    tables: int
    total_rows: int


class TableInfo(BaseModel):
    name: str
    row_count: int
    columns: list[str]
    description: str


class SchemaResponse(BaseModel):
    tables: list[TableInfo]


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None


class NewChatResponse(BaseModel):
    session_id: str


class ChatHistoryMessage(BaseModel):
    role: str
    content: str


class ChatHistoryResponse(BaseModel):
    session_id: str
    messages: list[ChatHistoryMessage]
