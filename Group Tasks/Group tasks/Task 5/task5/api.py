import logging
import os
import shutil
import time
from collections import OrderedDict
from pathlib import Path
from threading import RLock
from uuid import uuid4
from fastapi import FastAPI, Depends, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from . import inputs, workflow
from .schemas import Query, ReportRequest
from .report_agent import plan_report
from .pdf_renderer import render_pdf
from memory_cache import get_history, remember, cache_key, get_cached, put_cached, invalidate_cache, clear_session

BASE = Path(__file__).resolve().parent.parent
load_dotenv(BASE / "app.env")
DATA_DIR = Path(os.getenv("APP_DATA_DIR", str(BASE / "runtime")))
REPORT_DIR = DATA_DIR / "reports"
MAX_UPLOAD = 20 * 1024 * 1024
_responses = OrderedDict()
_reports = OrderedDict()
_lock = RLock()
log = logging.getLogger(__name__)


def authorize(authorization: str | None = Header(default=None)):
    import hmac
    token = os.getenv("APP_API_TOKEN")
    if token and not hmac.compare_digest(authorization or "", "Bearer " + token):
        raise HTTPException(401, "A valid application token is required.")


app = FastAPI(title="Week 8 Document Intelligence", version="2.0.0")


@app.get("/health")
def health():
    return {"status": "ok", "mode": workflow.mode(), "stt_model": Path(os.getenv("STT_MODEL", "base")).name,
            "ocr": "RapidOCR Latin/Chinese", "report_planner": os.getenv("REPORT_PLANNER", "rules"),
            "llm_configured": bool(os.getenv("OPENROUTER_API_KEY")) and os.getenv("OPENROUTER_API_KEY") not in {"put_your_key_here", "your_api_key_here"}, "cloud_deployed": False}


@app.get("/")
def home():
    return FileResponse(BASE / "static" / "index.html")


def read_upload(file):
    try:
        data = file.file.read(MAX_UPLOAD + 1)
    finally:
        file.file.close()
    if not data:
        raise HTTPException(400, "The uploaded file is empty.")
    if len(data) > MAX_UPLOAD:
        raise HTTPException(413, "Maximum upload size is 20 MB.")
    return data


def source_name(name):
    return Path((name or "source").replace("\\", "/")).name[:120]


@app.post("/upload", dependencies=[Depends(authorize)])
def upload(file: UploadFile = File(...)):
    name = source_name(file.filename)
    if Path(name).suffix.lower() not in {".pdf", ".docx", ".txt"}:
        raise HTTPException(400, "Upload PDF, DOCX or TXT; use image input for OCR.")
    data = read_upload(file)
    directory = DATA_DIR / "uploads" / uuid4().hex
    directory.mkdir(parents=True, exist_ok=True)
    try:
        path = directory / name
        path.write_bytes(data)
        count = workflow.ingest_document(path)
        invalidate_cache()
        return {"filename": name, "chunks": count, "status": "indexed", "mode": workflow.mode()}
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except Exception as exc:
        log.exception("Document indexing failed")
        raise HTTPException(503, "Document indexing failed. Check models and configuration.") from exc
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def ask_question(payload):
    question = payload.question.strip()
    if not question:
        raise HTTPException(422, "Question cannot be blank.")
    history = get_history(payload.session_id)
    key = cache_key(question, history)
    result = get_cached(key)
    cached = result is not None
    if result is None:
        try:
            result = workflow.answer(question, history)
        except Exception as exc:
            log.exception("Question workflow failed")
            raise HTTPException(503, "Question workflow unavailable. Check OpenRouter and retrieval models, or explicitly select extractive mode.") from exc
        put_cached(key, result)
    remember(payload.session_id, question, result["answer"])
    response_id = uuid4().hex
    record = {**result, "question": question, "session_id": payload.session_id,
              "response_id": response_id, "cached": cached, "mode": workflow.mode()}
    with _lock:
        _responses[response_id] = record
        if len(_responses) > 128:
            _responses.popitem(last=False)
    return record


@app.post("/ask", dependencies=[Depends(authorize)])
def ask(payload: Query):
    return ask_question(payload)


@app.post("/voice-query", dependencies=[Depends(authorize)])
def voice_query(file: UploadFile = File(...), session_id: str = Form("default", min_length=1, max_length=128)):
    data = read_upload(file)
    try:
        adapted = inputs.transcribe(data)
    except inputs.InputError as exc:
        raise HTTPException(422, str(exc)) from exc
    except inputs.AdapterUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc
    if len(adapted["text"]) > 4000:
        raise HTTPException(422, "Transcript is too long for a question. Use a shorter recording.")
    result = ask_question(Query(question=adapted["text"], session_id=session_id))
    return {**result, "transcription": adapted["text"], "input_type": "voice", "input_metadata": adapted["metadata"]}


@app.post("/image-query", dependencies=[Depends(authorize)])
def image_query(file: UploadFile = File(...), question: str = Form(..., min_length=1, max_length=4000),
                session_id: str = Form("default", min_length=1, max_length=128)):
    if not question.strip():
        raise HTTPException(422, "Question cannot be blank.")
    data = read_upload(file)
    try:
        adapted = inputs.extract_image(data)
        name = "image_" + uuid4().hex[:8] + "_" + source_name(file.filename)
        count = workflow.ingest_pages([{"document": name, "page": 1, "text": adapted["text"]}])
    except inputs.InputError as exc:
        raise HTTPException(422, str(exc)) from exc
    except inputs.AdapterUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc
    except Exception as exc:
        log.exception("Image processing failed")
        raise HTTPException(503, "Image OCR or indexing failed.") from exc
    invalidate_cache()
    result = ask_question(Query(question=question, session_id=session_id))
    return {**result, "ocr_text": adapted["text"], "input_type": "image", "source": name,
            "chunks": count, "input_metadata": adapted["metadata"]}


def cleanup_reports():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    with _lock:
        for file in REPORT_DIR.glob("*.pdf"):
            if file.stat().st_mtime < time.time() - 86400:
                file.unlink(missing_ok=True)
                _reports.pop(file.stem, None)


@app.post("/reports", dependencies=[Depends(authorize)])
def reports(payload: ReportRequest):
    with _lock:
        record = _responses.get(payload.response_id)
    if not record or record["session_id"] != payload.session_id:
        raise HTTPException(404, "Response not found in this session. Ask the question again.")
    style, planner, note = plan_report(record, payload.design_brief, payload.style)
    report_id = uuid4().hex
    cleanup_reports()
    path = REPORT_DIR / (report_id + ".pdf")
    try:
        render_pdf(path, payload.title, record["question"], record, style)
    except Exception as exc:
        path.unlink(missing_ok=True)
        log.exception("PDF generation failed")
        raise HTTPException(503, "PDF generation failed. Verify bundled fonts and report content.") from exc
    with _lock:
        _reports[report_id] = payload.session_id
        if len(_reports) > 128:
            old_id, _ = _reports.popitem(last=False)
            (REPORT_DIR / (old_id + ".pdf")).unlink(missing_ok=True)
    return {"report_id": report_id, "download_url": f"/reports/{report_id}",
            "style": style.model_dump(), "planner": planner, "note": note}


@app.get("/reports/{report_id}", dependencies=[Depends(authorize)])
def download_report(report_id: str, session_id: str = "default"):
    if len(report_id) != 32 or any(c not in "0123456789abcdef" for c in report_id):
        raise HTTPException(404, "Report not found.")
    cleanup_reports()
    with _lock:
        owner = _reports.get(report_id)
    path = REPORT_DIR / (report_id + ".pdf")
    if owner != session_id or not path.is_file():
        raise HTTPException(404, "Report not found or expired.")
    return FileResponse(path, media_type="application/pdf", filename=f"document-report-{report_id[:8]}.pdf")


@app.delete("/sessions/{session_id}", dependencies=[Depends(authorize)])
def reset_session(session_id: str):
    clear_session(session_id)
    with _lock:
        for key in [k for k, v in _responses.items() if v["session_id"] == session_id]:
            _responses.pop(key, None)
        for key in [k for k, v in _reports.items() if v == session_id]:
            _reports.pop(key, None)
            (REPORT_DIR / (key + ".pdf")).unlink(missing_ok=True)
    return {"status": "cleared", "session_id": session_id}
