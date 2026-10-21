"""
ingest.py — turn the files in data/ into a searchable database.

Run it:    python ingest.py

This is also the ONLY thing you re-run to make the chatbot answer about
YOUR documents (Chapter 5): drop your PDF, .md, or .txt files into data/,
run this script, restart the app. No other code changes.
"""

import sys

if sys.version_info < (3, 10):
    sys.exit(
        "\nThis course needs Python 3.10 or newer — you're on "
        f"{sys.version.split()[0]}.\n"
        "Create a 3.10+ virtual environment first; see SETUP.md in the project root.\n"
    )

import os
import shutil
import tempfile

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

_HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(_HERE, "data")
# chroma_db must live somewhere WRITABLE. On Streamlit Cloud the repo mount is
# read-only, so default to the OS temp dir; override with CHROMA_DB_DIR if set.
DB_DIR = os.environ.get(
    "CHROMA_DB_DIR", os.path.join(tempfile.gettempdir(), "roya_cafe_chroma_db")
)


def load_documents():
    """Read every supported file in data/ into LangChain Documents.

    We read PDFs with pypdf and text files directly — no langchain-community
    (it's being sunset). Each Document carries its file name as `source`, which
    is what citations display later.
    """
    docs = []
    for name in sorted(os.listdir(DATA_DIR)):
        path = os.path.join(DATA_DIR, name)
        lower = name.lower()
        if lower.endswith(".pdf"):
            text = "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
            docs.append(Document(page_content=text, metadata={"source": name}))
        elif lower.endswith((".md", ".txt")):
            with open(path, encoding="utf-8") as f:
                docs.append(Document(page_content=f.read(), metadata={"source": name}))
        else:
            print(f"  skipping {name} (not a .pdf, .md, or .txt file)")
    return docs


def build_database(force: bool = False):
    """Split documents into chunks, embed them, and save the database.

    Race-safe: builds into a private staging dir, then atomically renames it
    into place. If a database already exists, skips the rebuild — so two
    processes starting at once (as Streamlit Cloud does on cold start) can't
    delete the directory out from under each other.
    """
    # Already built? Don't touch it (unless a manual rebuild forces it).
    if os.path.exists(DB_DIR) and os.listdir(DB_DIR):
        if not force:
            print(f"Database already present at {DB_DIR}/ — skipping rebuild.")
            return
        shutil.rmtree(DB_DIR, ignore_errors=True)

    print(f"Reading files from {DATA_DIR}/ …")
    docs = load_documents()
    if not docs:
        raise SystemExit(f"No documents found in {DATA_DIR}/ — add some files first!")

    # Split long documents into bite-size, overlapping chunks
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = splitter.split_documents(docs)

    # Keep just the file name as the source — this is what citations display
    for chunk in chunks:
        chunk.metadata["source"] = os.path.basename(chunk.metadata.get("source", "unknown"))

    print(f"  {len(docs)} document(s) → {len(chunks)} chunks")

    # Build into a PRIVATE staging dir next to DB_DIR (same filesystem, so the
    # rename below is atomic). Concurrent builders never share a directory.
    print("Embedding chunks and building the database…")
    parent = os.path.dirname(os.path.abspath(DB_DIR)) or "."
    os.makedirs(parent, exist_ok=True)
    staging = tempfile.mkdtemp(prefix=".chroma_build_", dir=parent)
    Chroma.from_documents(
        chunks,
        embedding=GoogleGenerativeAIEmbeddings(model="gemini-embedding-001"),
        persist_directory=staging,
        collection_metadata={"hnsw:space": "cosine"},
    )

    # Atomically claim DB_DIR. If another process already won the race, keep theirs.
    try:
        os.replace(staging, DB_DIR)
        print(f"Done! Database saved to {DB_DIR}/ — now run:  python -m streamlit run app.py")
    except OSError:
        shutil.rmtree(staging, ignore_errors=True)
        print(f"Database already built by another process — using {DB_DIR}/")


if __name__ == "__main__":
    build_database(force=True)
