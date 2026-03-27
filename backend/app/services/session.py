import uuid
from dataclasses import dataclass, field


@dataclass
class ChatSession:
    session_id: str
    messages: list[dict] = field(default_factory=list)
    history: list[tuple[str, str]] = field(default_factory=list)


class ChatSessionManager:
    """Manages in-memory chat sessions."""

    def __init__(self):
        self._sessions: dict[str, ChatSession] = {}

    def create_session(self) -> str:
        """Create a new chat session and return its ID."""
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = ChatSession(session_id=session_id)
        return session_id

    def get_session(self, session_id: str) -> ChatSession | None:
        """Get a session by ID, or None if not found."""
        return self._sessions.get(session_id)

    def add_message(self, session_id: str, role: str, content: str) -> None:
        """Add a message to a session's message history."""
        session = self._sessions.get(session_id)
        if session:
            session.messages.append({"role": role, "content": content})

    def add_history(self, session_id: str, query: str, answer: str) -> None:
        """Add a query-answer pair to the conversation history (for refinement context)."""
        session = self._sessions.get(session_id)
        if session:
            session.history.append((query, answer[:500]))
