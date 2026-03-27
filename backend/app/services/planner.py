import logging

from langchain_openai import ChatOpenAI

from app.config import AppConfig
from app.prompts import PLANNER_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)


class PlannerService:
    """Decomposes complex queries into step-by-step execution plans."""

    def __init__(self, config: AppConfig):
        self._llm = ChatOpenAI(
            model=config.openai_model,
            temperature=0,
            api_key=config.openai_api_key,
        )

    def plan(self, query: str, schema_context: str) -> str:
        """Break a complex user query into logical execution steps."""
        prompt = PLANNER_PROMPT_TEMPLATE.format(schema_context=schema_context, query=query)

        logger.debug("Planning query: %s", query)
        response = self._llm.invoke(prompt)
        return response.content
