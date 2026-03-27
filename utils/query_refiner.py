from langchain_openai import ChatOpenAI


def refine_query(user_query, conversation_history):
    """Refine a follow-up query using conversation context to make it self-contained."""
    if not conversation_history:
        return user_query

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    recent = conversation_history[-3:]
    history_text = "\n".join(f"Q: {q}\nA: {a}" for q, a in recent)

    prompt = f"""Given this conversation history:
{history_text}

The user now asks: "{user_query}"

If this is a follow-up question that references previous results (e.g., "filter that", "now show", "break it down"),
rewrite it as a self-contained question. If it's already self-contained, return it unchanged.

Return ONLY the rewritten question, nothing else."""

    response = llm.invoke(prompt)
    return response.content.strip()
