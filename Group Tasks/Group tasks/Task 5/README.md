# Week 8 Document Intelligence

Task 5 extends the Week 7 Multi-Agent Document Intelligence system with microphone/recording queries, image OCR and dynamically designed PDF reports. Task 6 infrastructure is in `infra/terraform/`.

The existing Retriever → Analyst → Answer Agent workflow remains available in `APP_MODE=llm`. A separate, explicitly labeled `APP_MODE=extractive` lets reviewers exercise the complete media/API/PDF flow without an API key. It returns matching source passages and does not pretend to perform LLM reasoning or establish evidence sufficiency.

## Install and run

Use Python 3.11 or 3.12 in a new virtual environment. Initial model downloads require Internet. CPU inference is supported; a GPU is not required.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-task5.txt
Copy-Item app.env.example app.env
```

Edit `app.env`: add your own OpenRouter key and set a model available to your account. `openrouter/free` is the baseline example, not a promise of continued availability or quota. No credentials are included in the package. Then:

```powershell
python -m uvicorn api:app --host 127.0.0.1 --port 8000 --workers 1
```

Open http://127.0.0.1:8000 and http://127.0.0.1:8000/docs. Use one worker because the original memory/cache and the response/report registries are process-local.

For a no-key demonstration, set `APP_MODE=extractive` in `app.env` before starting. It retains document loading and the real OCR/STT/PDF adapters, but replaces embedding/LLM reasoning with literal source-passage matching. For full retrieval and agent reasoning, use `APP_MODE=llm`; the first query may download embedding/reranking models.

## User workflow

1. Upload a PDF, DOCX or TXT source.
2. Ask a text question, record a microphone question, or upload a recording.
3. Alternatively, upload an image and a question. Its OCR text is indexed with an image-specific source ID and actually enters the evidence pipeline.
4. Review the answer, transcript/OCR text, sources, analysis and limitations.
5. Supply a report title and design instructions; generate and download the PDF.

Microphone capture uses the browser MediaRecorder API and requires localhost or HTTPS and browser permission. WAV/MP3/M4A/OGG/WebM files can be uploaded instead. PyAV decodes media on the server. Maximum upload is 20 MB; audio is limited during decoding to 120 seconds, and empty/silent audio is rejected. The default speech model is multilingual Faster-Whisper `base`, CPU INT8. `STT_MODEL=tiny` is useful for a smaller demonstration; accuracy varies by recording and language.

OCR uses RapidOCR ONNX with bundled recognition models, avoiding a system Tesseract dependency. Supported inputs are PNG/JPEG/WebP, up to 16 megapixels. The shipped recognizer covers Latin/Chinese printed text; Arabic OCR is not supported by this release. Voice and the baseline multilingual text pipeline can accept Arabic, but that is not a claim that the OCR recognizer does.

## Report agent

The report agent receives the stored application response, user design brief and optional explicit style. It selects a validated design using the local rule-based planner by default. Set `REPORT_PLANNER=llm` to ask the existing OpenRouter adapter for a schema-validated design; on failure it uses the local planner and labels the fallback.

The agent can control font family (`sans`, `serif`, `mono`), body/heading size, color, page size, portrait/landscape, margins, spacing, line height and heading emphasis. It chooses landscape for numerical tables and responds to brief keywords. Example briefs:

- `formal serif purple landscape`
- `accessible large blue Letter`
- `compact mono green`

Exact overrides are available through the `style` object in `POST /reports`, documented by OpenAPI. Font paths cannot be supplied; numeric sizes are bounded. The renderer escapes user/model text, embeds licensed DejaVu fonts, supports pagination and repeated result-table headers, and carries sources and evidence limitations into the PDF. It never changes answer facts to fit a design. Short Arabic passages use reshaping/bidirectional support; complex mixed-direction tables need manual review.

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Readiness/configuration summary; does not claim external-model health |
| POST | `/upload` | Multipart document `file` |
| POST | `/ask` | JSON `question`, `session_id` |
| POST | `/voice-query` | Multipart audio `file`, `session_id`; transcribe and ask |
| POST | `/image-query` | Multipart image `file`, `question`, `session_id`; OCR, index and ask |
| POST | `/reports` | Stored `response_id`, `session_id`, title, design brief, optional style |
| GET | `/reports/{report_id}?session_id=...` | Download a report for its session |
| DELETE | `/sessions/{session_id}` | Clear that conversation, response records and report files |

```json
{"question":"What is the total revenue?","session_id":"demo"}
```

Use the returned `response_id` when requesting a report:

```json
{"response_id":"<returned 32-character ID>","session_id":"demo","title":"Sales review","design_brief":"formal serif purple landscape"}
```

Report lookup never accepts a filesystem path. A report is tied to a stored response/session, capped at 128 active files and expired after 24 hours on report-endpoint access. Original upload files are deleted after indexing. In LLM mode, indexed source text persists in ChromaDB. In extractive mode it is held in memory only. Restarting clears the conversation/response/report registries; old report files expire on later cleanup.

## Verification

```powershell
python -m pytest tests_task5 -q
$env:OFFLINE_TESTS="1"
python -m pytest tests tests_task5 -q
```

The original test harness mocks embedding/reranking models in offline mode; baseline LLM tests also use mocks. New API contract tests mock OCR/STT only where stated, while decoding/silence/duration tests inspect actual audio bytes. Live local OCR and STT demonstrations are separate from those unit tests. `evidence/` records exact execution modes, actual JSON outputs, measured durations and generated example PDFs. No live external LLM success or cloud deployment is inferred from mock tests. See the verification summary for what actually ran.

`python scripts/live_demo.py` generates local media/API/report evidence using real OCR and speech recognition with explicit extractive answering. It needs the shipped samples and model download access. The supplied spoken sample is synthetic Windows TTS, labeled as such; it is not a recording of a team member. Unit-test outputs and real-model outputs are not interchangeable.

## Team and scope

See `TEAM_ROLES.md` for Person A/B/C module organization matching the work plans. Week 7 component attribution remains in `README_WEEK7.md`.

This version is a private shared-workspace application. Uploaded documents are shared across its users. Session IDs limit accidental response/report mixups but are not user authentication. Set `APP_API_TOKEN` to enable a shared bearer token; enter it in the UI access settings or supply `Authorization: Bearer ...`. Deploy only behind restricted ingress and HTTPS, with one worker. Multi-tenant identity/isolation, HA, persistent sessions, automatic backup/restore and public-service load testing are not implemented.

The separate Voice Agents project is not part of Tasks 5/6 and is not included as a completed deliverable here.

## References

- https://github.com/SYSTRAN/faster-whisper
- https://github.com/RapidAI/RapidOCR
- https://fastapi.tiangolo.com/tutorial/request-files/
- https://developer.hashicorp.com/terraform/language/tests/mocking
- Bundled font license: `task5/fonts/LICENSE.txt`
