import json
import logging

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessageChunk

from app.models.requests import ChatRequest
from app.models.responses import (
    ChatResponse,
    NewChatResponse,
    ChatHistoryResponse,
    ChatHistoryMessage,
)

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


@router.post("/stream")
async def chat_stream(body: ChatRequest, request: Request):
    """Stream the full plan + agent execution lifecycle via SSE."""
    session_manager = request.app.state.session_manager
    agent_service = request.app.state.agent_service
    planner_service = request.app.state.planner_service
    chart_service = request.app.state.chart_service
    refiner_service = request.app.state.refiner_service
    schema_text = request.app.state.schema_text

    session = session_manager.get_session(body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session_manager.add_message(body.session_id, "user", body.query)

    refined = refiner_service.refine(body.query, session.history)
    refined_query = refined if refined != body.query else None
    query_to_execute = refined if refined != body.query else body.query

    async def generate():
        # Phase 1: Stream plan
        plan_text = ""
        async for token in planner_service.stream_plan(query_to_execute, schema_text):
            plan_text += token
            yield f"data: {json.dumps({'type': 'plan', 'chunk': token})}\n\n"
        yield f"data: {json.dumps({'type': 'plan_done', 'plan': plan_text})}\n\n"

        # Phase 2: Stream agent execution
        final_content = ""
        async for msg_chunk, metadata in agent_service.stream_execute_query(
            query_to_execute, session.history
        ):
            if isinstance(msg_chunk, AIMessageChunk):
                if msg_chunk.tool_calls:
                    for tc in msg_chunk.tool_calls:
                        yield f"data: {json.dumps({'type': 'tool_call', 'name': tc['name'], 'args': str(tc.get('args', ''))})}\n\n"
                elif msg_chunk.content:
                    # Only stream tokens from the final answer node (not internal reasoning)
                    langgraph_node = metadata.get("langgraph_node", "")
                    if langgraph_node == "agent":
                        final_content += msg_chunk.content
                        yield f"data: {json.dumps({'type': 'agent', 'chunk': msg_chunk.content})}\n\n"
            elif hasattr(msg_chunk, 'content') and msg_chunk.content:
                # ToolMessage results
                yield f"data: {json.dumps({'type': 'tool_result', 'result': msg_chunk.content[:500]})}\n\n"

        # Phase 3: Build final response with chart
        result = final_content
        df = chart_service.parse_result(str(result))
        table_data = None
        chart_data = None

        if df is not None and len(df) >= 2:
            table_data = df.to_dict(orient="records")
            chart_data = chart_service.generate(df, query=body.query)

        session_manager.add_message(body.session_id, "assistant", result)
        session_manager.add_history(body.session_id, body.query, str(result))

        response = ChatResponse(
            answer=result,
            plan=plan_text,
            table_data=table_data,
            chart=chart_data,
            session_id=body.session_id,
            refined_query=refined_query,
        )
        yield f"data: {json.dumps({'type': 'result', 'data': response.model_dump()})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
