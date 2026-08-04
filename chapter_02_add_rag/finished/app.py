"""
app.py — your chatbot's web page (Chapter 2: now answering from your docs).

First build the database, then run, both from the project root:
    python ingest.py
    python -m streamlit run app.py

The agent (model + search tool) lives INLINE in this file for now. In
Chapter 3 we move the "brain" out into chatbot.py and slim this file back
down. Answers are still plain text — citations are the Chapter 3 reveal.
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
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.messages import AIMessage

from ingest import DB_DIR

RELEVANCE_THRESHOLD = 0.35   # keep only matches at least this relevant (0-1)

st.set_page_config(page_title="Roya's Imaginary Cafe Assistant", page_icon="☕")

# API key
try:
    if "GOOGLE_API_KEY" in st.secrets:
        os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
except Exception:
    pass

if not os.environ.get("GOOGLE_API_KEY"):
    st.error("Set the GOOGLE_API_KEY environment variable, then refresh.")
    st.stop()

if not os.path.exists(DB_DIR):
    st.error("No database found. Run `python ingest.py` first.")
    st.stop()


# --- The retrieval tool: how the agent looks things up ---

@tool
def search_documents(query: str) -> str:
    """Search the knowledge base for passages relevant to the query."""
    db = Chroma(
        persist_directory=DB_DIR,
        embedding_function=GoogleGenerativeAIEmbeddings(model="gemini-embedding-001"),
        collection_metadata={"hnsw:space": "cosine"},
    )
    scored = db.similarity_search_with_relevance_scores(query, k=4)
    results = [doc for doc, score in scored if score >= RELEVANCE_THRESHOLD]
    if not results:
        return "No matching passages found."
    return "\n\n---\n\n".join(
        f"[source: {doc.metadata.get('source', 'unknown')}]\n{doc.page_content}"
        for doc in results
    )


# --- The agent: model + tool + instructions ---

@st.cache_resource
def get_agent():
    return create_agent(
        model=init_chat_model("google_genai:gemini-3.5-flash", temperature=0),
        tools=[search_documents],
        system_prompt=(
            "You are the assistant for Roya's Imaginary Cafe. Always use the "
            "search_documents tool before answering, and base your answer only on "
            "what it returns. Be concise — lead with the answer, skip filler and "
            "apologies. If the search returns no passages, or the documents don't "
            "cover the question, say so honestly instead of guessing."
        ),
    )


agent = get_agent()


def message_text(message) -> str:
    """Gemini returns .content as a list of content blocks; pull out just the text
    so the answer never shows up as raw JSON. Works on whole messages and on the
    small chunks that .stream() yields."""
    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content
    return "".join(
        block.get("text", "") if isinstance(block, dict) else str(block)
        for block in (content or [])
    )


st.title("☕ Roya's Imaginary Cafe Assistant")
st.caption("Now answering from the documents in data/ — but can you trust it? (Chapter 3…)")

if "history" not in st.session_state:
    st.session_state.history = []

for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

question = st.chat_input("Ask about Roya's Imaginary Cafe…")

if question:
    st.session_state.history.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        # The agent runs a little loop: it calls the search tool, gets passages
        # back, then writes the answer. stream_mode="messages" streams every
        # message the agent produces — including the tool's result — so we keep
        # only the model's own messages (AIMessage covers its streaming chunks)
        # and let the answer type itself out.
        def token_stream():
            for token, _meta in agent.stream(
                {"messages": st.session_state.history}, stream_mode="messages"
            ):
                if not isinstance(token, AIMessage):
                    continue
                text = message_text(token)
                if text:
                    yield text

        answer = st.write_stream(token_stream())

    st.session_state.history.append({"role": "assistant", "content": answer})
