# ☕ Build Your Own AI Chatbot — Exercise Files

Exercise files for the LinkedIn Learning course. You'll build a production RAG
chatbot from an empty file: it answers from your documents, cites its sources,
declines honestly when it doesn't know, gets graded by an LLM judge, and ends up
live on a public URL.

Sample data is *Roya's Imaginary Cafe* — a fictional Cambridge, MA coffee shop.
In Chapter 5 you swap in documents you actually care about.

## Start here

1. **Set up your environment** — follow [`SETUP.md`](SETUP.md). Most "it doesn't
   work for me" problems are environment problems; that page is the golden path.
2. **Get a free API key** (no credit card) at https://aistudio.google.com/apikey
3. **Open the chapter you're on** and work in its `start_here/` folder.

## How the folders work

Each chapter has two folders:

- **`start_here/`** — where the chapter begins. Open this and build along.
- **`finished/`** — where the chapter ends. Check your work, or catch up.

Each chapter's `start_here/` is identical to the previous chapter's `finished/`,
so you can jump in at any chapter without having done the earlier ones.

| Chapter | What you build |
|---|---|
| `chapter_01_first_chatbot` | A chat UI wired to a model — from an empty `app.py` |
| `chapter_02_add_rag` | `ingest.py`, a vector database, and a search tool the agent can call |
| `chapter_03_citations_guardrails` | `chatbot.py` (the brain), a citation contract, clickable sources, logging middleware |
| `chapter_04_llm_judge` | A trace tool, a golden question set, and LLM judges for faithfulness and completeness |
| `chapter_05_ship_it` | Cloud-ready hardening, a public deploy, and the swap to your own documents |

## Running any chapter

```bash
cd chapter_02_add_rag/start_here        # or whichever chapter you're on

python -m pip install -r requirements.txt
export GOOGLE_API_KEY="AIza..."         # Windows PowerShell: $env:GOOGLE_API_KEY="AIza..."

python ingest.py                        # Chapter 2 onward — builds the document database
python -m streamlit run app.py
```

Two files start out **empty on purpose**, because you write them from scratch on
camera: `chapter_01_first_chatbot/start_here/app.py` and
`chapter_03_citations_guardrails/start_here/chatbot.py`.

## Also in here

- [`SETUP.md`](SETUP.md) — environment setup and troubleshooting
- [`STREAMING_AND_CITATIONS.md`](STREAMING_AND_CITATIONS.md) — optional deep dive
  for the curious: why streaming turns off when citations arrive, and how you'd
  keep both
- `chapter_05_ship_it/sample_swap_docs/` — the Roya Land demo documents used in
  Chapter 5, if you want to follow the swap before bringing your own

## A note on the API key

Your key goes in an environment variable, or in Streamlit Secrets when you
deploy — **never in the code, and never committed.** The `.gitignore` here is set
up to keep `.env` files and `secrets.toml` out of git, but the habit matters more
than the safety net.
