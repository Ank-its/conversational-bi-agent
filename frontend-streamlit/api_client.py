import os
import logging

import requests

logger = logging.getLogger(__name__)

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")


class APIClient:
    """HTTP client for communicating with the backend API."""

    def __init__(self, base_url: str = BACKEND_URL):
        self._base_url = base_url.rstrip("/")

    def health(self) -> dict:
        """Check backend health."""
        resp = requests.get(f"{self._base_url}/api/health", timeout=10)
        resp.raise_for_status()
        return resp.json()

    def new_chat(self) -> str:
        """Create a new chat session. Returns session_id."""
        resp = requests.post(f"{self._base_url}/api/chat/new", timeout=10)
        resp.raise_for_status()
        return resp.json()["session_id"]

    def chat(self, query: str, session_id: str) -> dict:
        """Send a chat query. Returns full ChatResponse dict."""
        resp = requests.post(
            f"{self._base_url}/api/chat",
            json={"query": query, "session_id": session_id},
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()

    def get_history(self, session_id: str) -> dict:
        """Get chat history for a session."""
        resp = requests.get(f"{self._base_url}/api/chat/{session_id}", timeout=10)
        resp.raise_for_status()
        return resp.json()

    def get_schema(self) -> dict:
        """Get database schema info."""
        resp = requests.get(f"{self._base_url}/api/schema", timeout=10)
        resp.raise_for_status()
        return resp.json()
