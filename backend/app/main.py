import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import AppConfig
from app.services.database import DatabaseService
from app.services.agent import AgentService
from app.services.planner import PlannerService
from app.services.chart import ChartService
from app.services.query_refiner import QueryRefinerService
from app.services.session import ChatSessionManager
from app.schema.metadata import get_schema_text
from app.routers import chat, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup, cleanup on shutdown."""
    config = AppConfig()

    logging.basicConfig(
        level=config.log_level,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    )
    logger = logging.getLogger(__name__)

    logger.info("Initializing services...")

    # Database
    db_service = DatabaseService(config)
    db_service.setup()

    # Services (dependency injection)
    agent_service = AgentService(config, db_service)
    planner_service = PlannerService(config)
    chart_service = ChartService(config)
    refiner_service = QueryRefinerService(config)
    session_manager = ChatSessionManager()
    schema_text = get_schema_text()

    # Store on app state for access in routers
    app.state.db_service = db_service
    app.state.agent_service = agent_service
    app.state.planner_service = planner_service
    app.state.chart_service = chart_service
    app.state.refiner_service = refiner_service
    app.state.session_manager = session_manager
    app.state.schema_text = schema_text

    logger.info("All services initialized successfully")
    yield
    logger.info("Shutting down")


app = FastAPI(
    title="Instacart BI Agent API",
    description="Conversational Business Intelligence agent for Instacart grocery data",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(health.router)
