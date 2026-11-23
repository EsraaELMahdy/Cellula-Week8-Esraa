"""Real local OCR/STT + API/PDF demonstration, with explicitly extractive answers."""
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import sys
import time
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ['APP_MODE'] = 'extractive'
os.environ.setdefault('STT_MODEL', 'tiny')
from fastapi.testclient import TestClient
from pypdf import PdfReader
from task5.api import app
from task5.pdf_renderer import render_pdf
from task5.schemas import ReportStyle

samples = ROOT / 'samples'
out = ROOT / 'evidence'
out.mkdir(exist_ok=True)
client = TestClient(app)
token = os.getenv('APP_API_TOKEN')
headers = {'Authorization': 'Bearer ' + token} if token else {}
session = 'real-local-media-demo'
record = {'timestamp_utc': datetime.now(timezone.utc).isoformat(), 'python': platform.python_version(),
          'answer_mode': 'extractive', 'external_llm_called': False, 'microphone_ui_exercised': False,
          'audio_origin': 'Synthetic Windows SAPI TTS; not human/team speech', 'steps': []}

def save_record():
    (out / 'live_demo.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')

def post(path, **kwargs):
    start = time.perf_counter()
    response = client.post(path, headers=headers, **kwargs)
    data = response.json()
    record['steps'].append({'endpoint': path, 'http_status': response.status_code,
                            'elapsed_seconds': round(time.perf_counter() - start, 4), 'output': data})
    save_record()
    response.raise_for_status()
    return data

image_path = samples / 'sales_image.png'
audio_path = samples / 'question.wav'
record['inputs'] = [{'name': p.name, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
                      'bytes': p.stat().st_size} for p in [image_path, audio_path]]
image_result = post('/image-query', data={'question': 'What is the total revenue?', 'session_id': session},
                    files={'file': (image_path.name, image_path.read_bytes(), 'image/png')})
assert '1200' in image_result['ocr_text'] and '1200' in image_result['answer']
voice_result = post('/voice-query', data={'session_id': session},
                    files={'file': (audio_path.name, audio_path.read_bytes(), 'audio/wav')})
assert voice_result['transcription'].strip() and '1200' in voice_result['answer']
for name, brief in [('sample_report_blue.pdf', 'accessible large blue Letter'),
                    ('sample_report_purple.pdf', 'formal serif purple landscape')]:
    report = post('/reports', json={'response_id': voice_result['response_id'], 'session_id': session,
                  'title': 'Quarterly Sales Evidence Review', 'design_brief': brief})
    response = client.get(report['download_url'], params={'session_id': session}, headers=headers)
    response.raise_for_status()
    (out / name).write_bytes(response.content)
    assert '1200' in ''.join(p.extract_text() for p in PdfReader(io.BytesIO(response.content)).pages)

start = time.perf_counter()
blank = client.post('/image-query', headers=headers, data={'question': 'What is the total?', 'session_id': session},
                    files={'file': ('blank.png', (samples / 'blank_image.png').read_bytes(), 'image/png')})
record['blank_image'] = {'http_status': blank.status_code, 'output': blank.json(),
                         'elapsed_seconds': round(time.perf_counter() - start, 4)}
assert blank.status_code == 422

fixture = {'answer': ('Synthetic layout fixture: this paragraph tests page wrapping and is not model output. ' * 140),
           'analysis': 'Layout-only fixture. No benchmark or real-world result is claimed.',
           'results': {'table': [{'sample': f'Fixture row {i}', 'value': 'Long field content ' * 5} for i in range(35)]},
           'sources': [{'document': 'synthetic_layout_fixture', 'page': 1}],
           'warnings': ['Synthetic content for pagination testing only.'], 'enough_evidence': False}
render_pdf(out / 'long_report_fixture.pdf', 'Synthetic Pagination Test', 'Test long content', fixture, ReportStyle())
record['long_fixture_pages'] = len(PdfReader(out / 'long_report_fixture.pdf').pages)
assert record['long_fixture_pages'] >= 3
arabic = {**fixture, 'answer': 'إجمالي الإيرادات في هذا المثال هو ١٢٠٠ دولار.',
          'analysis': 'هذا مثال اصطناعي لاختبار عرض النص العربي.', 'results': {}}
render_pdf(out / 'arabic_layout_fixture.pdf', 'Arabic Text Layout Fixture', 'Arabic layout check', arabic, ReportStyle())
save_record()
print(json.dumps({'ocr_text': image_result['ocr_text'], 'transcription': voice_result['transcription'],
                   'long_fixture_pages': record['long_fixture_pages'], 'blank_status': blank.status_code}, indent=2))
