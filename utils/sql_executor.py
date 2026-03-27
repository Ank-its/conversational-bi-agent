MAX_RETRIES = 2


def execute_query(agent, query, conversation_history=None):
    """Execute a natural language query via the SQL agent with retry on failure."""
    context = ""
    if conversation_history:
        recent = conversation_history[-3:]
        context = "Previous conversation:\n"
        for q, a in recent:
            context += f"Q: {q}\nA: {a[:300]}\n"
        context += "\n"

    full_prompt = f"""{context}User question: {query}

Answer the question by querying the database. Return the result clearly formatted."""

    for attempt in range(MAX_RETRIES + 1):
        try:
            # langgraph agent uses messages-based input
            result = agent.invoke(
                {"messages": [("human", full_prompt)]},
            )
            # Extract the final AI message content
            messages = result.get("messages", [])
            if messages:
                return messages[-1].content
            return str(result)
        except Exception as e:
            if attempt < MAX_RETRIES:
                print(f"  Retry {attempt + 1}/{MAX_RETRIES}: {e}")
                full_prompt = f"""The previous attempt failed with error: {e}
Please fix and retry.
Original question: {query}"""
            else:
                return f"Error after {MAX_RETRIES + 1} attempts: {e}"
