# ☕ Build Your Own AI Chatbot — Course Starter

This is the starter project for the LinkedIn Learning course. By the end,
this exact repo becomes **your** chatbot, answering questions about
**your** documents, live on a **public URL**.

The sample data is the handbook, product FAQ, store policies, an about page, and
a catering guide for *Roya's Imaginary
Cafe*, a fictional café in Cambridge, MA. You'll replace it with your own
files in Chapter 5.

---

## Quick Start (3 steps)

**1. Install**
```bash
python -m pip install -r requirements.txt
```

**2. Add your API key** (free, no credit card — Google AI Studio)

Get a key at https://aistudio.google.com/apikey, then:
```bash
# Mac / Linux
export GOOGLE_API_KEY="AIza..."

# Windows (PowerShell)
$env:GOOGLE_API_KEY="AIza..."
```

**3. Build the database, then run the app**
```bash
python ingest.py
python -m streamlit run app.py
```

Your browser opens to a working chatbot. Ask it:
*"Can I bring my dog inside?"* — and click the source under its answer.

---

## What each file does

| File | What it is | Built in |
|---|---|---|
| `app.py` | The chatbot's web page (Streamlit) | Ch 1, 3, 5 |
| `chatbot.py` | The brain: agent, search tool, citations, middleware | Ch 2–3 |
| `ingest.py` | Turns `data/` files (PDF + Markdown) into a searchable database | Ch 2 |
| `trace.py` | Shows one run step by step — tool call, results, answer | Ch 4 |
| `evaluate.py` | Two AI judges: *faithful* (backed by sources) + *complete* | Ch 4 |
| `test_questions.json` | Questions plus the golden `expected` answer each | Ch 4 |
| `data/` | The documents your bot knows about (incl. a PDF) | Ch 2, 5 |

**Joining mid-course?** In the course repo, each chapter's `finished/` folder is
its own complete, runnable project — start from the one for the chapter you want.

---

## Use your own documents (Chapter 5)

1. Delete the sample files in `data/` and drop in your own `.pdf`, `.md`,
   or `.txt` files.
2. Re-run `python ingest.py`
3. Restart the app. That's it — no code changes.

Tip: also update the title, caption, and `SYSTEM_PROMPT` so the bot
introduces itself as *your* assistant.

---

## Deploy to a public URL (Chapter 5)

We use **Streamlit Community Cloud** — free, no credit card, no servers.

1. Push this folder to a GitHub repository.
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in
   with GitHub.
3. Click **New app**, pick your repo, set the main file to `app.py`.
4. In **Advanced settings → Secrets**, paste:
   ```toml
   GOOGLE_API_KEY = "AIza..."
   ```
5. Click **Deploy**.

The first start takes a couple of minutes — the server builds the
document database automatically from `data/`. Then you have a URL you
can paste into Slack, a resume, or a LinkedIn post.

---

## Swapping AI providers

One line in `chatbot.py`:
```python
MODEL = "google_genai:gemini-3.5-flash"
# MODEL = "openai:gpt-4o-mini"            # add OPENAI_API_KEY + langchain-openai
# MODEL = "anthropic:claude-sonnet-4-6"   # add ANTHROPIC_API_KEY + langchain-anthropic
```
(Note: embeddings in `ingest.py` and `chatbot.py` use Gemini, so keep
`GOOGLE_API_KEY` set even if you swap the chat model.)

---

## Troubleshooting

**"No API key found"** — set the environment variable in the *same
terminal* you run Streamlit from, or it won't be visible to the app.

**"No database found"** — run `python ingest.py` first.

**Chroma / sqlite error on Streamlit Cloud** — if the deploy log mentions
an unsupported sqlite3 version, add `pysqlite3-binary` to
`requirements.txt` and put these three lines at the very top of `app.py`:
```python
__import__("pysqlite3")
import sys
sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
```

**Answers seem stale after changing documents** — `ingest.py` rebuilds
from scratch each run, so just re-run it and restart the app.

**Model name error from Gemini** — Google retires model names on a
schedule. If `gemini-3.5-flash` is rejected, check the current name at
https://ai.google.dev/gemini-api/docs/models and update the one string in
`chatbot.py` (`MODEL`).
