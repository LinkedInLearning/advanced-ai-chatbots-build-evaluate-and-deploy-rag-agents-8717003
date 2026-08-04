"""
app.py — your chatbot's web page.

Run it locally:    python -m streamlit run app.py
Deploy it:         push to GitHub, then share.streamlit.io (see README, Chapter 5)

This file is the chatbot's FACE. The brain lives in chatbot.py.
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

from ingest import DB_DIR

# ---------------------------------------------------------------------------
# Chapter 1 — Page setup and API key
# ---------------------------------------------------------------------------

st.set_page_config(page_title="Roya's Imaginary Cafe Assistant", page_icon="☕")

# Locally, the key comes from your environment (see README step 2).
# On Streamlit Community Cloud, it comes from the app's Secrets panel.
try:
    if "GOOGLE_API_KEY" in st.secrets:
        os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
except Exception:
    pass  # no secrets file locally — that's fine, we check the env var next

if not os.environ.get("GOOGLE_API_KEY"):
    st.error(
        "No API key found. Set the GOOGLE_API_KEY environment variable "
        "(or add it to Secrets if you're on Streamlit Cloud), then refresh."
    )
    st.stop()

# ---------------------------------------------------------------------------
# Chapter 2 — Make sure the document database exists
# ---------------------------------------------------------------------------

if not os.path.exists(DB_DIR):
    st.error("No database found. Run `python ingest.py` first.")
    st.stop()

from chatbot import build_agent, safe_answer  # imported after the key is set


@st.cache_resource  # build the agent once, not on every click
def get_agent():
    return build_agent()


agent = get_agent()

# ---------------------------------------------------------------------------
# Chapters 1, 3, 5 — The chat interface
# ---------------------------------------------------------------------------

st.title("☕ Roya's Imaginary Cafe Assistant")
st.caption(
    "Ask me about Roya's Imaginary Cafe — our menu, policies, and employee "
    "handbook. Every answer shows its sources."
)

if "history" not in st.session_state:
    st.session_state.history = []


def show_citations(citations: list[dict]):
    """Chapter 3 — render each citation as a clickable, expandable source.
    De-duplicates so the same passage never shows up twice."""
    seen = set()
    for c in citations:
        key = (c["source"], c["quote"])
        if key in seen:
            continue
        seen.add(key)
        with st.expander(f"📄 Source: {c['source']}"):
            # Prefix every line with "> " so multi-paragraph quotes stay fully quoted
            quote = c["quote"].replace("\n", "\n> ")
            st.markdown(f"> {quote}")

# Replay the conversation so far
for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        show_citations(msg.get("citations", []))

# Handle a new question
question = st.chat_input("Ask a question about the documents…")

if question:
    st.session_state.history.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        with st.spinner("Searching the documents…"):
            # Send the whole conversation so the bot remembers context
            messages = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.history
            ]
            # safe_answer() never returns None, so the UI can't crash here
            response = safe_answer(agent.invoke({"messages": messages}))

        st.write(response.answer)
        citations = [{"source": c.source, "quote": c.quote} for c in response.citations]
        show_citations(citations)

    st.session_state.history.append(
        {"role": "assistant", "content": response.answer, "citations": citations}
    )
