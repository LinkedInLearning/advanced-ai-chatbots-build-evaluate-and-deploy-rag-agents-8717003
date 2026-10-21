# SETUP — get a clean, working environment (do this once)

Most "the code doesn't work for me" problems are environment problems, not code
problems: the wrong Python version, or a second Python (often Anaconda) hijacking
your commands. This page is the one golden path that avoids both. Follow it top to
bottom — and don't skip the **verification gate** in the middle.

You need two things: **Python 3.10 or newer**, and a **free Google AI Studio API
key** (no credit card). Get the key at https://aistudio.google.com/apikey.

---

## ⚠️ If you use Anaconda — read this first

If your terminal prompt shows `(base)`, Anaconda is active and will quietly take
over the `python`, `pip`, and `streamlit` commands even after you make a virtual
environment. That's the single most common way this setup goes sideways. Turn it
off before you start:

```bash
conda deactivate
conda config --set auto_activate_base false
```

Open a new terminal and confirm `(base)` is gone before continuing. (No Anaconda?
Skip this — nothing to do.)

---

## 1. Check your Python version

```bash
python3 --version
```

If that says **3.10 or higher**, you're set — use `python3` below. If it's older
(macOS often ships 3.9), install a newer one from https://www.python.org/downloads
(3.11 is a safe choice) and use the full path to it in the next step, e.g.
`/Library/Frameworks/Python.framework/Versions/3.11/bin/python3`.

## 2. Create and activate a virtual environment

A virtual environment is a private box of packages for this project, so it can't
fight with anything else on your machine.

```bash
python3 -m venv .venv                 # use your 3.10+ python here
source .venv/bin/activate             # Windows PowerShell: .venv\Scripts\Activate.ps1
```

Your prompt should now start with `(.venv)`.

## 3. ✅ THE VERIFICATION GATE — do not skip

Before installing anything, confirm the environment is really the one that's
active. Run all three:

```bash
which python
python --version
python -c "import sys; print(sys.prefix)"
```

All three must be true:
- `which python` points **inside your project's `.venv`** (not `/opt/anaconda3`, not `/usr/bin`)
- `python --version` is **3.10 or newer**
- `sys.prefix` ends in **`.venv`**

If any of those is wrong, stop and fix it now — installing on top of a wrong
environment is what causes the confusing errors later. Most often the fix is the
Anaconda step above, then rebuild: `deactivate`, `rm -rf .venv`, and redo step 2
with an explicit 3.10+ python path.

## 4. Install the dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Always write `python -m pip` (not bare `pip`) — it guarantees you're installing
into the environment that's active, so PATH confusion can't bite you.

A clean install ends with a list of installed packages and **no** lines saying
"already satisfied … /opt/anaconda3" and **no** uninstalls. If you see those, the
packages went to the wrong place — go back to step 3.

## 5. Run it

```bash
# Chapter 2 onward only — build the document database first:
python -m streamlit run app.py
```

(In Chapter 1 there are no documents, so just the `streamlit` line. From Chapter 2
on, run `python ingest.py` once before `python -m streamlit run app.py`.)

Use `python -m streamlit run` rather than bare `streamlit run`, for the same reason
as `python -m pip`: it runs the streamlit that belongs to your active environment.

---

## Quick fixes for the usual suspects

- **`ModuleNotFoundError: No module named 'streamlit.cli'`** — a stale, system-wide
  Streamlit is running instead of yours. You're not in your `.venv` (step 3), or
  you typed bare `streamlit` instead of `python -m streamlit`.
- **`No module named streamlit` (or langchain)** — the install didn't land in this
  environment, or a previous install failed partway. Re-check step 3, then redo
  step 4.
- **pip prints "Ignored the following versions … Requires-Python >=3.10"** — your
  Python is too old (3.9 or below). Redo step 1 with a 3.10+ interpreter.
- **`No API key found`** — set the key in the *same terminal* you run from:
  `export GOOGLE_API_KEY="AIza..."` (Windows PowerShell: `$env:GOOGLE_API_KEY="AIza..."`).
- **Anaconda warnings about other packages after installing** — you installed into
  `(base)` by mistake. Do the Anaconda step, rebuild the venv (step 2), reinstall.

A `.python-version` file (`3.11`) ships in each folder; if you use **pyenv**, it
will select 3.11 automatically (install it once with `pyenv install 3.11`). If you
don't use pyenv, the file is harmless and ignored.
