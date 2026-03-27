from pydantic_settings import BaseSettings
from pydantic import Field


class AppConfig(BaseSettings):
    openai_api_key: str = Field(..., description="OpenAI API key")
    openai_model: str = Field(default="gpt-4o-mini", description="OpenAI model name")
    db_path: str = Field(default="instacart.db", description="DuckDB database file path")
    data_dir: str = Field(default="data", description="Directory containing CSV data files")
    log_level: str = Field(default="INFO", description="Logging level")
    max_retries: int = Field(default=2, description="Max retries for agent execution")
    chart_dpi: int = Field(default=100, description="Chart image DPI")
    max_result_rows: int = Field(default=30, description="Max rows to display in results")

    model_config = {"env_file": ".env", "extra": "ignore"}
