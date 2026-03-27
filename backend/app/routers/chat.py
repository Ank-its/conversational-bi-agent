import logging

from fastapi import APIRouter, Request, HTTPException

from app.models.requests import ChatRequest
from app.models.responses import (
    ChatResponse,
    NewChatResponse,
    ChatHistoryResponse,
    ChatHistoryMessage,
    ErrorResponse,
)
from app.exceptions import SessionNotFoundError, QueryExecutionError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/new", response_model=NewChatResponse)
def new_chat(request: Request):
    """Start a new chat session."""
    session_manager = request.app.state.session_manager
    session_id = session_manager.create_session()
    logger.info("Created new chat session: %s", session_id)
    return NewChatResponse(session_id=session_id)


@router.get("/{session_id}", response_model=ChatHistoryResponse)
def get_chat_history(session_id: str, request: Request):
    """Get chat history for a session."""
    session_manager = request.app.state.session_manager
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return ChatHistoryResponse(
        session_id=session_id,
        messages=[ChatHistoryMessage(**m) for m in session.messages],
    )


@router.post("", response_model=ChatResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
def chat(body: ChatRequest, request: Request):
    """Send a query and get a response with optional table data and chart."""
    session_manager = request.app.state.session_manager
    agent_service = request.app.state.agent_service
    planner_service = request.app.state.planner_service
    chart_service = request.app.state.chart_service
    refiner_service = request.app.state.refiner_service
    schema_text = request.app.state.schema_text

    # Validate session
    session = session_manager.get_session(body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Store user message
    session_manager.add_message(body.session_id, "user", body.query)

    # Refine follow-up queries
    refined = refiner_service.refine(body.query, session.history)
    refined_query = refined if refined != body.query else None

    query_to_execute = refined if refined != body.query else body.query

    # Plan
    plan = planner_service.plan(query_to_execute, schema_text)

    # Execute
    try:
        result = agent_service.execute_query(query_to_execute, session.history)
    except QueryExecutionError as e:
        logger.error("Query execution failed: %s", e)
        raise HTTPException(status_code=400, detail=str(e))

    # Parse table data
    df = chart_service.parse_result(str(result))
    table_data = None
    chart_data = None

    if df is not None and len(df) >= 2:
        table_data = df.to_dict(orient="records")
        chart_data = chart_service.generate(df, query=body.query)

    # Store assistant message and history
    session_manager.add_message(body.session_id, "assistant", result)
    session_manager.add_history(body.session_id, body.query, str(result))

    return ChatResponse(
        answer=result,
        plan=plan,
        table_data=table_data,
        chart=chart_data,
        session_id=body.session_id,
        refined_query=refined_query,
    )
