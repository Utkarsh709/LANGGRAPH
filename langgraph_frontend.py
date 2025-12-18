import streamlit as st
from langgraph_backend import chatbot
from langchain_core.messages import HumanMessage
import uuid

st.set_page_config(page_title="LangGraph Chatbot")


# ------------------------------
# UTILITY FUNCTIONS
# ------------------------------
def generate_thread_id():
    return str(uuid.uuid4())


def reset_chat():
    thread_id = generate_thread_id()
    st.session_state["thread_id"] = thread_id
    add_thread(thread_id)
    st.session_state["message_history"] = []


def add_thread(thread_id):
    if thread_id not in st.session_state["chat_threads"]:
        st.session_state["chat_threads"].append(thread_id)


def load_conversation(thread_id):
    state = chatbot.get_state(config={"configurable": {"thread_id": thread_id}})
    messages = state.values.get("messages", [])
    return messages


# ------------------------------
# SESSION STATE INITIALIZATION
# ------------------------------
if "message_history" not in st.session_state:
    st.session_state["message_history"] = []

if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = generate_thread_id()

if "chat_threads" not in st.session_state:
    st.session_state["chat_threads"] = []

add_thread(st.session_state["thread_id"])


# ------------------------------
# SIDEBAR UI
# ------------------------------
st.sidebar.title("LangGraph Chatbot")

if st.sidebar.button("New Chat"):
    reset_chat()

st.sidebar.header("My Conversations")

for thread_id in st.session_state["chat_threads"][::-1]:
    if st.sidebar.button(thread_id):
        st.session_state["thread_id"] = thread_id

        # Load stored messages from the LangGraph backend
        raw_messages = load_conversation(thread_id)
        temp_messages = []

        for m in raw_messages:
            role = "user" if isinstance(m, HumanMessage) else "assistant"
            temp_messages.append({"role": role, "content": m.content})

        st.session_state["message_history"] = temp_messages


# ------------------------------
# DISPLAY OLD MESSAGES
# ------------------------------
for msg in st.session_state["message_history"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# ------------------------------
# USER INPUT
# ------------------------------
user_input = st.chat_input("Type here...")

if user_input:
    # Store user message
    st.session_state["message_history"].append(
        {"role": "user", "content": user_input}
    )

    with st.chat_message("user"):
        st.markdown(user_input)

    # ------------------------------
    # STREAM AI RESPONSE
    # ------------------------------
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""

        for message_chunk, metadata in chatbot.stream(
            {"messages": [HumanMessage(content=user_input)]},
            config={"configurable": {"thread_id": st.session_state["thread_id"]}},
            stream_mode="messages"
        ):
            chunk_text = message_chunk.content
            full_response += chunk_text
            placeholder.markdown(full_response)

    # Store assistant message
    st.session_state["message_history"].append(
        {"role": "assistant", "content": full_response}
    )
