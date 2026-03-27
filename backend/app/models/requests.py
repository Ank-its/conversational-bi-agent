from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="User's natural language query")
    session_id: str = Field(..., description="Chat session ID")


class NewChatRequest(BaseModel):
    pass
