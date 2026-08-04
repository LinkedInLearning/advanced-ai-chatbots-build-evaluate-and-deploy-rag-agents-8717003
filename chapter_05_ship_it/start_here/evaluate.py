import sys

if sys.version_info < (3, 10):
    sys.exit(
        "\nThis course needs Python 3.10 or newer — you're on "
        f"{sys.version.split()[0]}.\n"
        "Create a 3.10+ virtual environment first; see SETUP.md in the project root.\n"
    )

import json
import logging
from datetime import datetime

from langchain.chat_models import init_chat_model
from chatbot import build_agent, safe_answer, message_text

JUDGE_MODEL = "google_genai:gemini-3.5-flash"

FAITHFUL_PROMPT = """\
You are a strict grader checking whether a chatbot answer is FAITHFUL to its sources.

Question: {question}
Chatbot answer: {answer}
Quotes the chatbot cited as evidence:
{quotes}

PASS only if every factual claim in the answer is supported by the quotes, OR the
answer honestly says the documents don't cover the question.
FAIL if any claim goes beyond the quotes, or the citations are empty while the
answer still makes factual claims.

Reply with exactly one word: PASS or FAIL.
"""


def _verdict(prompt: str) -> bool:
    judge = init_chat_model(JUDGE_MODEL, temperature=0)
    return message_text(judge.invoke(prompt)).strip().upper().startswith("PASS")


def faithful(question, answer, citations) -> bool:
    quotes = "\n".join(f'- [{c.source}] "{c.quote}"' for c in citations) or "(none)"
    return _verdict(FAITHFUL_PROMPT.format(question=question, answer=answer, quotes=quotes))


COMPLETE_PROMPT = """\
You are checking whether a chatbot answer is COMPLETE.

Question: {question}
The answer SHOULD convey these facts (the golden answer): {expected}
The chatbot's answer: {answer}

PASS if the chatbot's answer conveys the key facts in the golden answer (wording
may differ). If the golden answer says the bot should decline because the info
isn't available, PASS when the chatbot honestly declines.
FAIL if the answer omits or contradicts a key fact from the golden answer.

Reply with exactly one word: PASS or FAIL.
"""


def complete(question, answer, expected) -> bool:
    return _verdict(COMPLETE_PROMPT.format(question=question, answer=answer, expected=expected))


HISTORY_FILE = "eval_history.jsonl"

# Quiet the bot's per-call logs during a batch — we want the scoreboard, not the play-by-play.
logging.getLogger("cafe-bot").setLevel(logging.WARNING)


def main():
    questions = json.load(open("test_questions.json", encoding="utf-8"))
    agent = build_agent()
    n_faithful = n_complete = 0

    for i, item in enumerate(questions, 1):
        q = item["question"]
        response = safe_answer(agent.invoke({"messages": [{"role": "user", "content": q}]}))
        f_ok = faithful(q, response.answer, response.citations)
        c_ok = complete(q, response.answer, item["expected"])
        n_faithful += f_ok
        n_complete += c_ok
        print(f"Q{i}  faithful {'✅' if f_ok else '❌'}  complete {'✅' if c_ok else '❌'}  | {q}")
        print(f"     ↳ {response.answer[:110]}")
        if not c_ok:
            print(f"       expected: {item['expected']}")

    total = len(questions)
    print(f"\nFaithful: {n_faithful}/{total}    Complete: {n_complete}/{total}")

    row = {"ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
           "faithful": n_faithful, "complete": n_complete, "total": total}
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


if __name__ == "__main__":
    main()
