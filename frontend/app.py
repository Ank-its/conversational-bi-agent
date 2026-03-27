import base64
import io

import pandas as pd
import streamlit as st

from api_client import APIClient

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


# --- Initialize ---
def init_state():
    if "client" not in st.session_state:
        st.session_state.client = APIClient()

    if "chats" not in st.session_state:
        st.session_state.chats = {}
        st.session_state.active_chat = None
        st.session_state.chat_counter = 0
        _new_chat()


def _new_chat():
    """Create a new chat session via the backend API."""
    client: APIClient = st.session_state.client
    try:
        session_id = client.new_chat()
    except Exception:
        session_id = f"local_{st.session_state.chat_counter + 1}"

    st.session_state.chat_counter += 1
    st.session_state.chats[session_id] = {
        "title": "New Chat",
        "messages": [],
    }
    st.session_state.active_chat = session_id
    return session_id


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
        chat_data = st.session_state.chats[chat_id]
        is_active = chat_id == st.session_state.active_chat
        label = chat_data["title"]
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
session_id = st.session_state.active_chat
client: APIClient = st.session_state.client

# Render existing messages
for msg in chat["messages"]:
    with st.chat_message(msg["role"]):
        content = msg["content"]
        has_table = msg.get("table_data") is not None
        # Strip inline pipe-tables from text when we have structured table data
        if has_table:
            cleaned = [l for l in content.split("\n")
                       if not ("|" in l.strip() and not l.strip().startswith("("))]
            content = "\n".join(cleaned).strip()
        if content:
            st.markdown(content)
        if has_table:
            st.dataframe(pd.DataFrame(msg["table_data"]), use_container_width=True)
        if msg.get("chart_base64"):
            image_bytes = base64.b64decode(msg["chart_base64"])
            st.image(io.BytesIO(image_bytes))

# Handle new input
user_input = st.chat_input("Ask a question about Instacart data...")

pending = st.session_state.pop("pending_query", None)
if pending and not user_input:
    user_input = pending

if user_input:
    if not chat["messages"] or chat["messages"][-1].get("content") != user_input or chat["messages"][-1].get("role") != "user":
        chat["messages"].append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    if chat["title"] == "New Chat":
        chat["title"] = user_input[:40] + ("..." if len(user_input) > 40 else "")

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = client.chat(user_input, session_id)
            except Exception as e:
                st.error(f"Error communicating with backend: {e}")
                response = None

        if response:
            # Show refined query if different
            if response.get("refined_query"):
                st.caption(f"Interpreted as: *{response['refined_query']}*")

            # Show plan
            with st.expander("Query Plan", expanded=False):
                st.markdown(response.get("plan", ""))

            # Show answer — if we have structured table_data, strip the
            # inline table from the answer text to avoid duplicate rendering.
            table_data = response.get("table_data")
            answer_text = response["answer"]
            if table_data:
                # Remove pipe-formatted tables from the answer text
                cleaned_lines = []
                for line in answer_text.split("\n"):
                    stripped = line.strip()
                    # Skip pipe-table rows and separator lines
                    if "|" in stripped and not stripped.startswith("("):
                        continue
                    if stripped and set(stripped.replace("+", "").replace("-", "").strip()) <= {""}:
                        continue
                    cleaned_lines.append(line)
                answer_text = "\n".join(cleaned_lines).strip()

            if answer_text:
                st.markdown(answer_text)

            if table_data:
                st.dataframe(pd.DataFrame(table_data), use_container_width=True)

            # Show chart
            chart_data = response.get("chart")
            chart_base64 = None
            if chart_data and chart_data.get("image_base64"):
                chart_base64 = chart_data["image_base64"]
                image_bytes = base64.b64decode(chart_base64)
                st.image(io.BytesIO(image_bytes))

            # Store assistant message
            chat["messages"].append({
                "role": "assistant",
                "content": response["answer"],
                "table_data": table_data,
                "chart_base64": chart_base64,
            })
