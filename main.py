import os
from dotenv import load_dotenv

# Load environment variables before any LLM imports
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from db.setup_duckdb import setup_database
from agents.sql_agent import create_agent
from agents.planner import decompose_query
from agents.chart_agent import generate_chart, parse_result_to_df
from utils.sql_executor import execute_query
from utils.query_refiner import refine_query
from schema.schema_index import get_schema_text


def run():
    # Step 1: Ensure database is set up
    print("Setting up database...")
    setup_database()

    # Step 2: Create SQL agent
    print("Initializing SQL agent...")
    agent = create_agent()

    # Step 3: Load schema context (plain text, no vector index overhead)
    schema_text = get_schema_text()

    print("\n" + "=" * 60)
    print("  Conversational BI Agent - Instacart Dataset")
    print("=" * 60)
    print("Ask questions in plain English about the Instacart grocery data.")
    print("Examples:")
    print("  - What are the top 10 most ordered products?")
    print("  - Which departments have the highest reorder rate?")
    print("  - Show me order distribution by hour of day")
    print("  - How many users have placed more than 50 orders?")
    print("Type 'exit' to quit.\n")

    conversation_history = []  # list of (query, answer) tuples

    while True:
        try:
            user_query = input("Ask: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_query:
            continue
        if user_query.lower() in ("exit", "quit", "q"):
            print("Goodbye!")
            break

        # Step 4: Refine follow-up queries using conversation context
        refined_query = refine_query(user_query, conversation_history)
        if refined_query != user_query:
            print(f"  (Interpreted as: {refined_query})")

        # Step 5: Plan the query approach
        print("\nPlanning...")
        plan = decompose_query(refined_query, schema_text)
        print(f"Plan:\n{plan}\n")

        # Step 6: Execute via SQL agent
        print("Executing...")
        result = execute_query(agent, refined_query, conversation_history)
        print(f"\nResult:\n{result}")

        # Step 7: Try to generate a chart
        df = parse_result_to_df(str(result))
        if df is not None and len(df) >= 2:
            chart_path = generate_chart(df, query=user_query)
            if chart_path:
                print(f"\nChart saved: {chart_path}")
        else:
            print("  (No tabular data detected for charting)")

        # Step 8: Store in conversation history
        conversation_history.append((user_query, str(result)[:500]))

        print("\n" + "-" * 40)


if __name__ == "__main__":
    run()
