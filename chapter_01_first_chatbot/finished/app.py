"""
app.py — your chatbot's web page (Chapter 1: the plain chatbot).

Run it locally:    python -m streamlit run app.py

No documents yet — just you and the model. Chapter 2 gives it your docs.
This is the file you build by hand, line by line, in video 1.3.
"""

import sys

if sys.version_info < (3, 10):
    sys.exit(
        "\nThis course needs Python 3.10 or newer — you're on "
        f"{sys.version.split()[0]}.\n"
        "Create a 3.10+ virtual environment first; see SETUP.md in the project root.\n"
    )

import os

import streamlit as st
from langchain.chat_models import init_chat_model

st.set_page_config(page_title="My First Chatbot", page_icon="💬")

# Locally, the key comes from your environment (see README step 2).
# On Streamlit Community Cloud, it comes from the app's Secrets panel.
try:
    if "GOOGLE_API_KEY" in st.secrets:
        os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
except Exception:
    pass  # no secrets file locally — that's fine, we check the env var next

if not os.environ.get("GOOGLE_API_KEY"):
    st.error("Set the GOOGLE_API_KEY environment variable, then refresh.")
    st.stop()

# The model — one line, swappable to any provider
model = init_chat_model("google_genai:gemini-3.5-flash")


def reply_text(message) -> str:
    """Gemini returns .content as a list of content blocks; older models return a
    plain string. Either way, pull out just the text so we never show raw JSON.
    Works on whole messages AND on the little chunks that .stream() yields."""
    content = message.content
    if isinstance(content, str):
        return content
    return "".join(
        block.get("text", "") if isinstance(block, dict) else str(block)
        for block in content
    )


st.title("💬 My First Chatbot")

if "history" not in st.session_state:
    st.session_state.history = []

# Replay the conversation so far (survives Streamlit's top-to-bottom re-run)
for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

question = st.chat_input("Say something…")

if question:
    st.session_state.history.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        # Stream the reply so it types itself out. model.stream() yields little
        # chunks; we pull the text out of each one and hand them to
        # st.write_stream, which displays them live and returns the full text.
        def token_stream():
            for chunk in model.stream(st.session_state.history):
                yield reply_text(chunk)

        answer = st.write_stream(token_stream())

    st.session_state.history.append({"role": "assistant", "content": answer})
