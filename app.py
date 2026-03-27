import os
import streamlit as st
from dotenv import load_dotenv

# Load env before any LLM imports
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from db.setup_duckdb import setup_database
from agents.sql_agent import create_agent
from agents.planner import decompose_query
from agents.chart_agent import generate_chart, parse_result_to_df
from utils.sql_executor import execute_query
from utils.query_refiner import refine_query
from schema.schema_index import get_schema_text

# --- Page config ---
st.set_page_config(
    page_title="Instacart BI Agent",
    page_icon="📊",
    layout="wide",
)

# --- Custom CSS ---
st.markdown("""
<style>
    .stChatMessage { max-width: 100%; }
    .block-container { padding-top: 2rem; padding-bottom: 0rem; }
    [data-testid="stSidebar"] { min-width: 250px; max-width: 300px; }
    .chat-title { font-size: 0.85rem; color: #888; padding: 4px 8px; border-radius: 4px;
                  cursor: pointer; margin-bottom: 2px; white-space: nowrap;
                  overflow: hidden; text-overflow: ellipsis; }
    .chat-title:hover { background: #f0f0f0; }
    .chat-title.active { background: #e3e8f0; font-weight: 600; }
</style>
""", unsafe_allow_html=True)


# --- Initialize session state ---
def init_state():
    if "chats" not in st.session_state:
        st.session_state.chats = {}  # chat_id -> {title, messages, history}
        st.session_state.active_chat = None
        st.session_state.chat_counter = 0
        _new_chat()

    if "agent" not in st.session_state:
        with st.spinner("Setting up database..."):
            setup_database()
        with st.spinner("Initializing AI agent..."):
            st.session_state.agent = create_agent()
            st.session_state.schema_text = get_schema_text()


def _new_chat():
    st.session_state.chat_counter += 1
    chat_id = f"chat_{st.session_state.chat_counter}"
    st.session_state.chats[chat_id] = {
        "title": f"New Chat",
        "messages": [],  # list of {role, content, table, chart}
        "history": [],   # list of (query, answer) for conversational memory
    }
    st.session_state.active_chat = chat_id
    return chat_id


def get_active_chat():
    if st.session_state.active_chat is None or st.session_state.active_chat not in st.session_state.chats:
        _new_chat()
    return st.session_state.chats[st.session_state.active_chat]


init_state()

# --- Sidebar ---
with st.sidebar:
    st.markdown("### Instacart BI Agent")
    st.caption("Ask questions about grocery data")

    if st.button("+ New Chat", use_container_width=True, type="primary"):
        _new_chat()
        st.rerun()

    st.divider()
    st.markdown("**Chat History**")

    for chat_id in reversed(list(st.session_state.chats.keys())):
        chat = st.session_state.chats[chat_id]
        is_active = chat_id == st.session_state.active_chat
        label = chat["title"]
        if is_active:
            label = f"▸ {label}"
        if st.button(label, key=f"btn_{chat_id}", use_container_width=True,
                     type="secondary" if not is_active else "primary"):
            st.session_state.active_chat = chat_id
            st.rerun()

    st.divider()
    st.markdown("**Sample Questions**")
    samples = [
        "What are the top 10 most ordered products?",
        "Which departments have the highest reorder rate?",
        "Show order distribution by hour of day",
        "How many users placed more than 50 orders?",
        "What aisles have highest reorder rate vs avg basket position?",
    ]
    for s in samples:
        if st.button(s, key=f"sample_{s[:20]}", use_container_width=True):
            chat = get_active_chat()
            chat["messages"].append({"role": "user", "content": s})
            st.session_state.pending_query = s
            st.rerun()

# --- Main chat area ---
chat = get_active_chat()

# Render existing messages
for msg in chat["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("table") is not None:
            st.dataframe(msg["table"], use_container_width=True)
        if msg.get("chart") is not None and os.path.exists(msg["chart"]):
            st.image(msg["chart"])

# Handle new input
user_input = st.chat_input("Ask a question about Instacart data...")

# Check for pending query from sample buttons
pending = st.session_state.pop("pending_query", None)
if pending and not user_input:
    user_input = pending

if user_input:
    # Add user message if not already added (sample buttons pre-add it)
    if not chat["messages"] or chat["messages"][-1].get("content") != user_input or chat["messages"][-1].get("role") != "user":
        chat["messages"].append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    # Update chat title from first query
    if chat["title"] == "New Chat":
        chat["title"] = user_input[:40] + ("..." if len(user_input) > 40 else "")

    # Process query
    with st.chat_message("assistant"):
        agent = st.session_state.agent
        schema_text = st.session_state.schema_text

        # Refine follow-ups
        with st.spinner("Thinking..."):
            refined = refine_query(user_input, chat["history"])
            if refined != user_input:
                st.caption(f"Interpreted as: *{refined}*")

            # Plan
            plan = decompose_query(refined, schema_text)

        # Show plan in expander
        with st.expander("Query Plan", expanded=False):
            st.markdown(plan)

        # Execute
        with st.spinner("Querying database..."):
            result = execute_query(agent, refined, chat["history"])

        # Display result text
        st.markdown(result)

        # Try to parse table
        df = parse_result_to_df(str(result))
        table_data = None
        chart_path = None

        if df is not None and len(df) >= 2:
            table_data = df
            st.dataframe(df, use_container_width=True)

            # Generate chart
            chart_path = generate_chart(df, query=user_input)
            if chart_path and os.path.exists(chart_path):
                st.image(chart_path)

        # Store assistant message
        chat["messages"].append({
            "role": "assistant",
            "content": result,
            "table": table_data,
            "chart": chart_path,
        })

        # Update conversation history
        chat["history"].append((user_input, str(result)[:500]))
