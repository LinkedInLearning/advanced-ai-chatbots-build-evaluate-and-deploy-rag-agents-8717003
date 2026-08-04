# Sample swap documents — Roya Land

These are the demo files used in **Video 5.3 — Make it answer about YOUR
documents**. They describe *Roya Land*, an imaginary theme park.

They are **not** part of the chatbot's data. They live here so you can follow
along with the swap without having to invent a document set first.

## How to use them

From `chapter_05_ship_it/start_here/` (or your own working copy):

```bash
rm data/*.md data/*.pdf                 # remove the cafe corpus
cp ../sample_swap_docs/roya-land-*.md data/
python ingest.py                        # rebuild the map from the new files
python -m streamlit run app.py
```

Then update the two places that name the bot:

- `app.py` — `st.set_page_config(page_title=...)` and `st.title(...)`
- `chatbot.py` — the first line of `SYSTEM_PROMPT`

Everything below that first prompt line stays exactly as it is. The rules about
always searching, citing precisely, and declining honestly are good behavior
regardless of subject.

Try asking: **"What's the most exciting ride in Roya Land?"**

## Use your own instead

That's the real point of the exercise. Drop any `.pdf`, `.md`, or `.txt` files
into `data/`, re-run `ingest.py`, and the same machine becomes an assistant for
whatever you care about.
