from langchain_openai import ChatOpenAI


def decompose_query(user_query, schema_context=""):
    """Break a complex user query into logical execution steps."""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    prompt = f"""You are a SQL query planner for an e-commerce grocery database (Instacart).

Available tables and relationships:
{schema_context}

Break this user question into a clear step-by-step SQL execution plan.
For each step, specify which tables are needed and what type of operation (join, aggregate, filter, etc.).

User question: {user_query}

Output a numbered plan (1-3 steps max). Be specific about table names and columns."""

    response = llm.invoke(prompt)
    return response.content
