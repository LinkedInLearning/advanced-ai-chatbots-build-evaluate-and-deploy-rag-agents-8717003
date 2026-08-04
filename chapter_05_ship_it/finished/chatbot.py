"""
chatbot.py — the brain of your chatbot.

This file is built across Chapters 2 and 3 of the course:
  Chapter 2: the retrieval tool and the agent (search + answer)
  Chapter 3: structured citations and middleware

The UI (app.py) and the grader (evaluate.py) both import from here,
so the "brain" lives in exactly one place.
"""

import sys

if sys.version_info < (3, 10):
    sys.exit(
        "\nThis course needs Python 3.10 or newer — you're on "
        f"{sys.version.split()[0]}.\n"
        "Create a 3.10+ virtual environment first; see SETUP.md in the project root.\n"
    )

import logging

from pydantic import BaseModel, Field

from langchain.agents import create_agent
from langchain.agents.middleware import before_model
from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# ---------------------------------------------------------------------------
# Chapter 3 — Logging
# A small, friendly logger so YOU can watch what the bot is doing in your
# terminal: when it searches, what it finds, and when it calls the model.
# (Run the app, ask a question, and watch these lines appear.)
# ---------------------------------------------------------------------------

logger = logging.getLogger("cafe-bot")
if not logger.handlers:                       # guard so reruns don't pile up handlers
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(asctime)s  cafe-bot  %(message)s", "%H:%M:%S"))
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

from ingest import DB_DIR   # single source of truth — defined once in ingest.py

# The ONE line you change to switch AI providers.
# Examples:  "google_genai:gemini-3.5-flash"   "openai:gpt-4o-mini"   "anthropic:claude-sonnet-4-6"
MODEL = "google_genai:gemini-3.5-flash"

RELEVANCE_THRESHOLD = 0.35   # keep only matches at least this relevant (0-1)


# ---------------------------------------------------------------------------
# Chapter 3 — Citations
# A "contract" the model must follow: every answer ships with its evidence.
# ---------------------------------------------------------------------------

class Citation(BaseModel):
    """One piece of evidence behind an answer."""
    source: str = Field(description="The file name the quote came from")
    quote: str = Field(description="The exact sentence(s) copied from that file")


class AnswerWithCitations(BaseModel):
    """What the chatbot must return for every question."""
    answer: str = Field(description="A friendly, complete answer to the question")
    citations: list[Citation] = Field(
        description="Every source passage the answer is based on"
    )


# ---------------------------------------------------------------------------
# Chapter 2 — The retrieval tool
# This is how the agent "looks things up" in your documents.
# ---------------------------------------------------------------------------

def get_database() -> Chroma:
    """Open the vector database that ingest.py created."""
    embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")
    return Chroma(persist_directory=DB_DIR, embedding_function=embeddings,
                  collection_metadata={"hnsw:space": "cosine"})


@tool
def search_documents(query: str) -> str:
    """Search the knowledge base for passages relevant to the query.
    Returns the top matching passages, each labeled with its source file."""
    logger.info('🔎 searching documents for: "%s"', query)
    scored = get_database().similarity_search_with_relevance_scores(query, k=4)
    results = [doc for doc, score in scored if score >= RELEVANCE_THRESHOLD]
    if not results:
        logger.info("   → no matching passages found")
        return "No matching passages found."
    found = ", ".join(sorted({doc.metadata.get("source", "unknown") for doc in results}))
    logger.info("   → %d passage(s) from: %s", len(results), found)
    return "\n\n---\n\n".join(
        f"[source: {doc.metadata.get('source', 'unknown')}]\n{doc.page_content}"
        for doc in results
    )


# ---------------------------------------------------------------------------
# Chapter 3 — Middleware
# A small function that runs every time the agent is about to call the model.
# This one just logs — but the same hook is where memory, guardrails,
# and PII filters plug in later (see Chapter 5's "next steps").
# ---------------------------------------------------------------------------

@before_model
def log_model_call(state, runtime):
    """Log a line each time the agent is about to call the model — this is the
    seam where guardrails, PII filters, or memory would plug in later."""
    logger.info("🤖 calling the model (%d messages in context)", len(state["messages"]))
    return None  # we're only observing, not changing anything


# ---------------------------------------------------------------------------
# Chapter 2 — The agent
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are the assistant for Roya's Imaginary Cafe. You are warm but to the point.

How to answer:
- ALWAYS use the search_documents tool before answering. Never answer from memory.
- Base every answer ONLY on the passages the tool returns.
- Be concise. Lead with the answer in a sentence or two. Use a short bullet list
  only when the user is genuinely asking for several options, and keep each item
  to one line. Do not pad with pleasantries, sales copy, or apologies about what
  the documents don't include.
- If the search returns no passages — including the "No matching passages found"
  reply when nothing clears the relevance bar — or the documents don't cover the
  question, say so in one sentence and return an empty citations list. Do not guess.

Citations:
- Cite ONLY the passages your answer actually relied on — usually one to three.
- Quote each source exactly, word-for-word from the passages.
- Never cite a passage that is only loosely related to the question. A passage you
  did not use in the answer does not belong in the citations.
"""


def build_agent():
    """Create the chatbot agent. Called once by app.py and evaluate.py."""
    return create_agent(
        model=init_chat_model(MODEL, temperature=0),
        tools=[search_documents],
        system_prompt=SYSTEM_PROMPT,
        response_format=AnswerWithCitations,
        # --- Extension seams (Chapter 5.4) ---------------------------------
        # The middleware list is THE place to add behavior without touching the
        # agent. Today it's just the logger. You grow the bot by writing a
        # @before_model (or @after_model) function and dropping it in here:
        #
        #   log_model_call,   # ← observability (built in this course)
        #   # memory-here     → conversation memory / summarization
        #   # pii-here        → redact personal info before it reaches the model
        #   # guardrails-here → input/output safety checks (content filters)
        #
        # Same list, more entries — that's the whole extension story.
        middleware=[log_model_call],
    )


# ---------------------------------------------------------------------------
# Safe accessor — use this everywhere instead of result["structured_response"]
#
# Once in a while the model finishes a turn without emitting the structured
# object through the proper channel. Reading result["structured_response"]
# directly then returns None, and the next line (response.answer) crashes.
# This helper catches that: it first tries to PARSE the model's final text as
# the JSON object (Gemini often returns the structured answer as raw JSON text,
# especially on an honest "not in the docs" decline), and only falls back to
# plain text if that fails — so the UI never shows a raw JSON blob or crashes.
# ---------------------------------------------------------------------------

def message_text(message) -> str:
    """Pull plain text out of a message, whatever shape its content is in.
    Gemini returns .content as a list of blocks; this flattens it to a string.
    Used by safe_answer() here and by the judge in evaluate.py."""
    content = getattr(message, "content", "") or ""
    if isinstance(content, list):  # some providers return a list of blocks
        return " ".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in content
        ).strip()
    return str(content).strip()


def safe_answer(result) -> AnswerWithCitations:
    """Return the agent's structured answer, with a graceful fallback."""
    structured = result.get("structured_response")
    if isinstance(structured, AnswerWithCitations):
        return structured

    # Fallback: the model finished without a populated structured_response.
    # With response_format set, its raw text is often the JSON object itself
    # (e.g. on an honest decline), so try to parse that into the schema first.
    messages = result.get("messages", [])
    text = message_text(messages[-1]) if messages else ""

    if text:
        try:
            cleaned = (
                text.strip()
                .removeprefix("```json")
                .removeprefix("```")
                .removesuffix("```")
                .strip()
            )
            return AnswerWithCitations.model_validate_json(cleaned)
        except Exception:
            pass  # not valid JSON for our schema — fall through to plain text

    return AnswerWithCitations(
        answer=text or "Sorry — I couldn't put together a sourced answer for that. "
                        "Try rephrasing your question.",
        citations=[],
    )
