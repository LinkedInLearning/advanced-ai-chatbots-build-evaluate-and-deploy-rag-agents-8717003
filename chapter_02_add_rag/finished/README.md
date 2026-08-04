# ☕ Build Your Own AI Chatbot — Course Starter

The starter project for the LinkedIn Learning course. By the end, this
exact repo becomes **your** chatbot, answering questions about **your**
documents, live on a **public URL**.

Sample data: *Roya's Imaginary Cafe* (Cambridge, MA), fictional. You'll
swap in your own files in Chapter 5.

## Run what you've built so far

```bash
python -m pip install -r requirements.txt
export GOOGLE_API_KEY="AIza..."   # Windows PowerShell: $env:GOOGLE_API_KEY="AIza..."

# Chapter 2 onward, build the document database first:
python ingest.py

python -m streamlit run app.py
```

Get a free key (no credit card) at https://aistudio.google.com/apikey.

> 📦 The full README — deploy steps, troubleshooting, swapping providers and
> your own data — lands in **Chapter 5**. This is the stub.
