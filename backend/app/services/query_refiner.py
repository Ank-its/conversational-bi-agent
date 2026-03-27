import logging

from langchain_openai import ChatOpenAI

from app.config import AppConfig
from app.prompts import QUERY_REFINER_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)


class QueryRefinerService:
    """Refines follow-up queries using conversation context to make them self-contained."""

    def __init__(self, config: AppConfig):
        self._llm = ChatOpenAI(
            model=config.openai_model,
            temperature=0,
            api_key=config.openai_api_key,
        )

    def refine(self, query: str, history: list[tuple[str, str]]) -> str:
        """Rewrite a follow-up query as a self-contained question using recent conversation context."""
        if not history:
            return query

        recent = history[-3:]
        history_text = "\n".join(f"Q: {q}\nA: {a}" for q, a in recent)

        prompt = QUERY_REFINER_PROMPT_TEMPLATE.format(history_text=history_text, query=query)

        response = self._llm.invoke(prompt)
        return response.content.strip()
