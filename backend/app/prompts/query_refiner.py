QUERY_REFINER_PROMPT_TEMPLATE = """Given this conversation history:
{history_text}

The user now asks: "{query}"

If this is a follow-up question that references previous results (e.g., "filter that", "now show", "break it down"),
rewrite it as a self-contained question. If it's already self-contained, return it unchanged.

Return ONLY the rewritten question, nothing else."""
