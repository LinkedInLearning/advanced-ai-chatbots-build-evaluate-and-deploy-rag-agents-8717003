"""
trace.py — see inside a single agent run (Chapter 4.1: observability).

Run it:    python trace.py "Can I bring my dog inside?"

This is the lightweight, no-account way to inspect what the agent actually did,
step by step: which tool it called and with what query, what the tool returned,
and the final answer with its citations. It just walks the messages the agent
produced — no extra service required.

Want a richer, hosted view instead? Set two environment variables and every run
is traced to the LangSmith web UI automatically (this is the "powerful, but needs
a free account" option):

    export LANGSMITH_TRACING=true
    export LANGSMITH_API_KEY="ls-..."
"""

import sys

if sys.version_info < (3, 10):
    sys.exit(
        "\nThis course needs Python 3.10 or newer — you're on "
        f"{sys.version.split()[0]}.\n"
        "Create a 3.10+ virtual environment first; see SETUP.md in the project root.\n"
    )

import textwrap

from chatbot import build_agent, safe_answer, message_text


def short(text: str, n: int = 300) -> str:
    text = text.strip().replace("\n", " ")
    return text if len(text) <= n else text[:n] + "…"


def trace(question: str):
    agent = build_agent()
    result = agent.invoke({"messages": [{"role": "user", "content": question}]})

    print(f"\n=== Tracing one run ===\nQUESTION: {question}\n")
    step = 0
    for msg in result["messages"]:
        mtype = getattr(msg, "type", msg.__class__.__name__)
        tool_calls = getattr(msg, "tool_calls", None)

        if mtype == "human":
            continue  # that's the question we already printed
        elif mtype == "ai" and tool_calls:
            for tc in tool_calls:
                step += 1
                print(f"STEP {step} — model decides to call a tool")
                print(f"   tool: {tc['name']}({tc.get('args', {})})\n")
        elif mtype == "tool":
            step += 1
            text = message_text(msg)
            print(f"STEP {step} — tool '{getattr(msg, 'name', 'search_documents')}' returned "
                  f"({len(text)} chars):")
            print(textwrap.indent(short(text, 400), "   ") + "\n")
        elif mtype == "ai":
            step += 1
            print(f"STEP {step} — model writes the final answer:")
            print(textwrap.indent(short(message_text(msg)), "   ") + "\n")

    # The structured result (answer + citations), via the same safe accessor the app uses
    answer = safe_answer(result)
    print("=== Structured result ===")
    print(f"answer:    {short(answer.answer)}")
    if answer.citations:
        print("citations:")
        for c in answer.citations:
            print(f"   [{c.source}] {short(c.quote, 100)}")
    else:
        print("citations: (none — the bot did not cite any source)")


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "Can I bring my dog inside the cafe?"
    trace(question)
