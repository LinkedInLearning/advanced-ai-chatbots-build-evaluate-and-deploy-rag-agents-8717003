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

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

DATA_DIR = "data"
DB_DIR = "chroma_db"


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


def build_database():
    """Split documents into chunks, embed them, and save the database."""
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

    # Start fresh each time so removed documents actually disappear
    if os.path.exists(DB_DIR):
        shutil.rmtree(DB_DIR)

    print("Embedding chunks and building the database…")
    Chroma.from_documents(
        chunks,
        embedding=GoogleGenerativeAIEmbeddings(model="gemini-embedding-001"),
        persist_directory=DB_DIR,
        collection_metadata={"hnsw:space": "cosine"},
    )
    print(f"Done! Database saved to {DB_DIR}/ — now run:  python -m streamlit run app.py")


if __name__ == "__main__":
    build_database()
