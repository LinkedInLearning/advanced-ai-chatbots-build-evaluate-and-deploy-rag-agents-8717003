# Streaming *and* citations — a note for the curious

> **Optional.** This course streams the answer in Chapters 1–2 (`st.write_stream`)
> so it types itself out, then turns streaming **off** in Chapter 3 the moment we
> add the citation contract. That's a deliberate trade, not a limitation — and if
> you want the typing effect back *with* citations, here's how, and why it's
> harder than it looks. None of this is required to finish the course.

## Why they fight in the first place

When we add `response_format=AnswerWithCitations`, the model stops writing prose
and starts writing **one JSON object**: `{"answer": "...", "citations": [...]}`.
Two things follow from that:

- **Streaming it shows JSON.** The tokens coming back are the JSON being typed
  out (`{"answer": "Our deca…`), not clean prose. Piping that to the screen looks
  broken.
- **The citations don't exist until the end.** The `citations` array is the last
  part of the object to be generated and closed, so there's nothing to render
  mid-stream — the structured result is only usable once the whole thing parses.

So the conflict isn't *streaming vs. citations* — it's *streaming vs. structured
output*. The Pydantic contract bundles the prose and the evidence into one
all-or-nothing blob. Keep that picture and the three fixes below make sense.

## Three ways to have both

### 1. Decouple — retrieve yourself, stream the answer, cite the chunks

Do the retrieval *before* you answer, so you already know the sources. Then stream
a plain answer (no `response_format`) over those passages, and show the chunks you
pulled. Streams perfectly.

```python
from chatbot import get_database, message_text
from langchain.chat_models import init_chat_model

model = init_chat_model("google_genai:gemini-3.5-flash", temperature=0)

# 1. Retrieve first — now you KNOW the sources before you answer.
docs = get_database().similarity_search(question, k=4)
context = "\n\n".join(f"[source: {d.metadata['source']}]\n{d.page_content}" for d in docs)

# 2. Stream a plain answer over that context (no response_format -> clean prose).
prompt = f"Answer using ONLY these passages.\n\n{context}\n\nQuestion: {question}"
answer = st.write_stream(message_text(chunk) for chunk in model.stream(prompt))

# 3. Show the sources you retrieved.
for d in docs:
    with st.expander(f"📄 Source: {d.metadata['source']}"):
        st.markdown(f"> {d.page_content[:300]}…")
```

**Trade-off:** your citations become "here are the passages we retrieved" instead
of "here is the exact quote the model says backs this claim." That's a *weaker*
guarantee than the `AnswerWithCitations` contract, and you give up the agent's
tool-calling autonomy (you're doing retrieval by hand). Simplest to get working.

### 2. Two passes — stream the prose, then a structured call for citations

Keep the precise contract by splitting the work: stream a plain answer, then make
a *second* call that returns the exact quotes for that answer.

```python
from chatbot import AnswerWithCitations

# Pass 1 — stream the answer (plain, no structured output).
answer = st.write_stream(message_text(chunk) for chunk in model.stream(prompt))

# Pass 2 — ask for citations on the answer you just streamed.
citer = init_chat_model("google_genai:gemini-3.5-flash", temperature=0)\
    .with_structured_output(AnswerWithCitations)
cited = citer.invoke(
    "Return the answer unchanged and the exact quotes from the passages that "
    f"back it.\n\nAnswer: {answer}\n\nPassages:\n{context}"
)
show_citations([{"source": c.source, "quote": c.quote} for c in cited.citations])
```

**Trade-off:** two model calls — roughly double the latency and cost — and the
citations are reconstructed after the fact rather than chosen as the answer is
written. The most faithful to the course's "verifiable, model-chosen citations"
promise *while* streaming.

### 3. Partial-JSON streaming — stream the structured output, parse as it grows

Stream the structured response and incrementally pull the `answer` field out of
the partial JSON as it fills, displaying only that text; render citations once the
object is complete. Some LangChain versions expose this via
`model.with_structured_output(...).stream(...)` yielding partial objects.

**Trade-off:** the partial JSON is invalid for most of the stream, so the parsing
is fiddly and behavior shifts across versions. Cleanest result, most fragile to
build — best left for when you control the exact stack.

## Which to use

- **For this course's promise** (every answer carries a verifiable, model-chosen
  quote), **non-streaming is the honest default** — which is why Chapter 3 reverts.
- **If you must have both in production:** reach for **two passes** when you need
  the precise quotes, or **decouple** when source-level citations are good enough
  and simplicity wins.

> Every sketch above is **illustrative**. Streaming behavior with structured
> output and a thinking model (Gemini) moves across LangChain / `langchain-google-genai`
> versions — verify on your stack before you rely on it, and never put an
> unverified streaming path near a recording.
