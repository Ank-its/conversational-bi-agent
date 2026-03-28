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

    async def stream_plan(self, query: str, schema_context: str):
        """Stream plan tokens as they are generated."""
        prompt = PLANNER_PROMPT_TEMPLATE.format(schema_context=schema_context, query=query)
        logger.debug("Streaming plan for query: %s", query)
        async for chunk in self._llm.astream(prompt):
            if chunk.content:
                yield chunk.content
