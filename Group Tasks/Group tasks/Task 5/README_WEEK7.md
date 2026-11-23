
# Week 7 — Multi-Agent Document Intelligence System

A unified project implementing **Part A (Retriever)**, **Part B (Analyst)**, and **Part C (Answer Agent, Orchestrator & API)**.

Users can upload PDF, DOCX, or TXT documents, ask questions, and receive evidence-grounded answers with document and page citations.

## Architecture

```text
Upload PDF / DOCX / TXT
    |
    v
Part A: Retriever
    - Document loading and cleaning
    - Chunking and embeddings
    - ChromaDB storage
    - Semantic + BM25 search
    - Reranking and context selection
    |
    v
Part B: Analyst
    - Evidence assessment
    - Feedback retrieval (max 3 rounds)
    - Table extraction
    - Calculations and statistics
    - Document comparisons
    |
    v
Part C: Answer Agent
    - Evidence-grounded answer
    - Citation formatting
    - Source formatting
    - Response formatting
    |
    v
Final Answer + Sources + Evidence Status
```

The **Orchestrator** coordinates the Retriever, Analyst, and Answer Agent.

FastAPI provides the browser interface and API endpoints. Chat memory and caching support follow-up questions.

## Requirements

- Python 3.10+
- Internet connection for initial model downloads
- OpenRouter API key for live LLM requests

## Installation

### 1. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 3. Configure OpenRouter

Copy the example configuration file:

```powershell
Copy-Item app.env.example app.env
```

On macOS/Linux:

```bash
cp app.env.example app.env
```

Edit `app.env`:

```env
OPENROUTER_API_KEY=your_api_key_here
```

Never commit or share your API key.

The initial execution may download embedding and reranking models.

## Run the Web Application

Start the FastAPI server:

```bash
python -m uvicorn api:app --reload
```

Open:

- Web UI: http://127.0.0.1:8000
- API Documentation: http://127.0.0.1:8000/docs
- Health Check: http://127.0.0.1:8000/health

### Using Document Chat

1. Choose a PDF, DOCX, or TXT file.
2. Click **Upload and index**.
3. Enter a question.
4. Click **Ask documents**.
5. Review the generated answer and citations.
6. Ask follow-up questions within the same session.
7. Click **New chat** to reset the conversation.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Web interface |
| GET | `/health` | Health check |
| POST | `/upload` | Upload and index documents |
| POST | `/ask` | Ask document-related questions |
| DELETE | `/sessions/{session_id}` | Clear chat history |

### Upload

`POST /upload`

Accepts PDF, DOCX, and TXT files up to 20 MB.

```bash
curl -F "file=@paper.pdf" http://127.0.0.1:8000/upload
```

### Ask

`POST /ask`

Example request:

```json
{
  "question": "What is the main result?",
  "session_id": "demo"
}
```

The response includes the generated answer, sources, evidence status, and analysis metadata.

### Reset Session

`DELETE /sessions/{session_id}`

Clears the specified conversation session.

## Part A — Retriever

Part A handles document ingestion and evidence retrieval.

It does not generate the final answer.

### Main Features

- PDF, DOCX, and TXT loading
- Text cleaning and chunking
- Multilingual embeddings
- ChromaDB vector storage
- Semantic search
- BM25 keyword search
- Metadata filtering
- Query rewriting
- Reranking
- Context selection

### Retriever Function

```python
retrieve(
    question,
    history=None,
    extra_query=None,
    max_chunks=5
)
```

Example output:

```python
[
    {
        "document": "paper.pdf",
        "page": 5,
        "score": 4.39,
        "content": "Relevant document text..."
    }
]
```

Higher reranker scores indicate better matches. Scores may be negative.

### Part A Modules

| File | Responsibility |
|---|---|
| `retriever/loader.py` | Load supported documents |
| `retriever/cleaner.py` | Clean extracted text |
| `retriever/chunker.py` | Create text chunks |
| `retriever/embedder.py` | Generate embeddings |
| `retriever/store.py` | ChromaDB storage |
| `retriever/ingest.py` | Document ingestion |
| `retriever/query_rewriter.py` | Rewrite contextual questions |
| `retriever/keyword.py` | BM25 search |
| `retriever/metadata_filter.py` | Filter by file/page |
| `retriever/reranker.py` | Rerank search results |
| `retriever/context_selector.py` | Select relevant context |
| `retriever/retrieve.py` | Main retrieval pipeline |

## Part B — Analyst

Part B processes evidence retrieved by Part A.

It checks whether the available information is sufficient and requests additional evidence when necessary.

### Main Features

- Evidence assessment
- Feedback retrieval loop
- Table extraction
- Mathematical calculations
- Statistical analysis
- Document comparisons
- Missing-information detection
- Error handling

### Analyst Function

```python
analyze(
    question,
    evidence,
    history=None,
    max_rounds=3
)
```

### Analyst Output

| Field | Description |
|---|---|
| `analysis` | Generated analysis |
| `enough_evidence` | Evidence sufficiency |
| `missing` | Missing information |
| `evidence` | Retrieved evidence |
| `rounds` | Additional retrieval rounds |
| `searches` | Additional search queries |
| `calculation` | Verified calculations |
| `table` | Extracted numerical data |
| `stats` | Statistical results |
| `comparison` | Document comparison |
| `warnings` | Errors and limitations |

### Feedback Loop

1. Evaluate retrieved evidence.
2. Identify missing information.
3. Generate a more specific search query.
4. Request additional evidence from the Retriever.
5. Remove duplicate evidence.
6. Re-evaluate the updated context.
7. Stop when sufficient evidence is available or the stopping conditions are reached.

The loop stops after the configured maximum rounds, repeated searches, or when no new evidence is found.

### Part B Modules

| File | Responsibility |
|---|---|
| `analyst/analyst.py` | Analysis and feedback loop |
| `analyst/calculator.py` | Safe arithmetic |
| `analyst/table_extractor.py` | Extract and validate numbers |
| `analyst/data_analysis.py` | Statistics and ranking |
| `analyst/comparison.py` | Document comparison |
| `analyst/search_more.py` | Additional retrieval |
| `analyst/llm.py` | OpenRouter integration |
| `analyst/utils.py` | Evidence utilities |

Calculations are performed using Python and verified source values rather than relying on LLM-generated arithmetic.

## Part C — Answer Agent, Orchestrator & API

Part C integrates the Retriever and Analyst into a complete document-question-answering application.

### Answer Agent

The Answer Agent produces the final response based on retrieved and analyzed evidence.

Its responsibilities include:

- Writing evidence-grounded answers
- Formatting document citations
- Formatting sources
- Formatting the final response
- Handling insufficient evidence

### Answer Agent Tools

1. **Citation Formatter:** Formats document and page references.
2. **Source Formatter:** Organizes supporting sources.
3. **Response Formatter:** Structures the final answer.

### Orchestrator

The Orchestrator coordinates the complete pipeline:

```text
User Question
     |
     v
Retriever
     |
     v
Analyst
     |
     v
Answer Agent
     |
     v
Final Cited Answer
```

It also integrates chat memory and response caching.

### Chat Memory

Conversation history enables contextual follow-up questions.

Example:

**Question 1:**

What are the three main responsibilities of Part C?

**Question 2:**

Explain the second responsibility from your previous answer.

The system can use the previous conversation to identify the intended responsibility.

### Caching

The application uses a bounded in-memory cache to reduce repeated processing.

The answer cache is invalidated after successful document uploads.

### Part C Modules

| File | Responsibility |
|---|---|
| `answer_agent/agent.py` | Final answer generation |
| `answer_agent/formatter.py` | Citation, source and response formatting |
| `orchestrator.py` | Agent coordination |
| `memory_cache.py` | Chat history and caching |
| `api.py` | FastAPI endpoints |
| `static/index.html` | Browser interface |
| `tests/test_part_c.py` | Part C tests |

## Command-Line Workflow

The original Parts A and B can also run independently.

```bash
python run_analyst.py paper.pdf "What is the average accuracy?"
```

### Python Example

```python
from retriever.ingest import ingest_file
from retriever.retrieve import retrieve
from analyst.analyst import analyze

ingest_file("paper.pdf")

question = "What is the average accuracy?"

evidence = retrieve(question)

result = analyze(
    question=question,
    evidence=evidence
)

print(result["analysis"])
```

## Testing

Run the complete test suite:

```bash
python -m pytest -v
```

### Latest Local Test Results

Test date: November 14, 2026

| Component | Passed |
|---|---:|
| Part A — Retriever | 26 |
| Part B — Analyst | 33 |
| Part C — Integration | 4 |
| **Total** | **63** |

**Results:**

- 63 passed
- 0 failed
- 14 deprecation warnings
- Execution time: 7.64 seconds

The warnings originated from third-party libraries using deprecated Python functionality.

Tests use mocked LLM responses and do not verify live model availability or answer accuracy.

### Offline Testing

Windows PowerShell:

```powershell
$env:OFFLINE_TESTS=1
python -m pytest tests -v
Remove-Item Env:OFFLINE_TESTS
```

Offline mode substitutes simple word matching for embedding and reranking models.

## Limitations

- Scanned PDFs require OCR, which is not included.
- DOCX page references default to page 1.
- The reranker is better suited to English.
- Numerical representations must match the source text.
- BM25 indexes are rebuilt for each question.
- Documents with identical filenames replace one another.
- ChromaDB data is stored locally.
- Chat memory and cache are not persistent across server restarts.
- Free OpenRouter model availability and quotas may change.
- Citations should be manually verified for critical use cases.

## Security

Never commit sensitive credentials or local runtime data.

Exclude the following from version control:

```gitignore
.env
app.env
.venv/
uploads/
chroma_db/
__pycache__/
.pytest_cache/
```

Keep `app.env.example` as a configuration template without real credentials.

If an API key is accidentally exposed, revoke it and generate a new key.

## Project Delivery Checklist

- [x] Part A — Retriever implemented
- [x] Part B — Analyst implemented
- [x] Part C — Answer Agent integrated
- [x] Orchestrator connected
- [x] FastAPI application running locally
- [x] Document upload tested
- [x] Document Q&A tested
- [x] Follow-up conversation tested
- [x] Markdown rendering tested
- [x] All 63 automated tests passed
- [ ] Verify API credentials are excluded from Git
- [ ] Final GitHub upload

## Conclusion

This project demonstrates a modular multi-agent document intelligence workflow combining document retrieval, evidence analysis, and grounded answer generation.

The system integrates the three project parts into a functional FastAPI application with a browser interface, contextual follow-up questions, source citations, and automated tests.



## Team Members

| Team Member | Project Part | Responsibilities |
|---|---|---|
| Esraa | Part A — Retriever | Document loading, preprocessing, chunking, embeddings, vector storage, semantic and keyword retrieval |
| Mariam | Part B — Analyst | Evidence analysis, calculations, table extraction, document comparison, and retrieval feedback loop |
| Alaa Boghdady | Part C — Answer Agent & Integration | Answer generation, source citations, orchestrator, chat memory, caching, FastAPI, and user interface |

### Project Overview

This project was developed collaboratively by three team members, each responsible for a core component of the Multi-Agent Document Intelligence System.

**Part A — Esraa:** Retriever Agent

**Part B — Mariam:** Analyst Agent

**Part C — Alaa Boghdady:** Answer Agent, Orchestrator & API

### System Workflow

Document Upload → Retriever → Analyst → Answer Agent → Final Answer with Citations
