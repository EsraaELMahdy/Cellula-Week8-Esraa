import io
import wave
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from pypdf import PdfReader
from task5 import api, workflow, inputs
from task5.report_agent import plan_report

@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv('APP_MODE', 'extractive')
    monkeypatch.delenv('APP_API_TOKEN', raising=False)
    monkeypatch.setattr(api, 'DATA_DIR', tmp_path)
    monkeypatch.setattr(api, 'REPORT_DIR', tmp_path / 'reports')
    workflow._pages.clear(); api._responses.clear(); api._reports.clear()
    from memory_cache import invalidate_cache, clear_session
    invalidate_cache()
    for s in ['default', 'a', 'b']: clear_session(s)

@pytest.fixture
def client(): return TestClient(api.app)

def seed(c):
    assert c.post('/upload',files={'file':('sales.txt',b'Sales total is 420 dollars. Revenue increased.')}).status_code==200
    return c.post('/ask',json={'question':'What is the sales total?','session_id':'a'}).json()

def test_text_evidence(client):
    r=seed(client)
    assert '420' in r['answer'] and r['sources'][0]['document']=='sales.txt'
    assert r['mode']=='extractive' and not r['enough_evidence']

@pytest.mark.parametrize('name,data,status',[('x.exe',b'123',400),('x.txt',b'',400),('x.txt',b'   ',422)])
def test_upload_errors(client,name,data,status):
    assert client.post('/upload',files={'file':(name,data)}).status_code==status

def test_upload_limit(client,monkeypatch):
    monkeypatch.setattr(api,'MAX_UPLOAD',5)
    assert client.post('/upload',files={'file':('x.txt',b'123456')}).status_code==413

@pytest.mark.parametrize('q',['','   ','x'*4001])
def test_invalid_question(client,q):
    assert client.post('/ask',json={'question':q}).status_code==422

def test_invalid_image(client):
    assert client.post('/image-query',data={'question':'sales'},files={'file':('fake.png',b'not image')}).status_code==422

def test_image_is_indexed_and_cited(client):
    with patch('task5.inputs.extract_image',return_value={'text':'Invoice total 780 dollars','metadata':{}}):
        r=client.post('/image-query',data={'question':'Invoice total','session_id':'a'},files={'file':('invoice.png',b'mocked adapter')})
    assert r.status_code==200
    j=r.json(); assert '780' in j['answer'] and j['source']==j['sources'][0]['document']

def test_voice_routes_to_question(client):
    seed(client)
    with patch('task5.inputs.transcribe',return_value={'text':'sales total','metadata':{'language':'en'}}):
        r=client.post('/voice-query',data={'session_id':'a'},files={'file':('question.wav',b'mocked adapter')})
    assert r.status_code==200 and '420' in r.json()['answer'] and r.json()['transcription']=='sales total'

def wav(seconds,sample=b'\0\0'):
    out=io.BytesIO()
    with wave.open(out,'wb') as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(16000);f.writeframes(sample*16000*seconds)
    return out.getvalue()

@pytest.mark.parametrize('data',[b'bad audio',wav(1)])
def test_corrupt_and_silent_audio(data):
    with pytest.raises(inputs.InputError): inputs.decode_audio(data)

def test_duration_bound():
    with pytest.raises(inputs.InputError,match='120-second'): inputs.decode_audio(wav(121,b'\1\1'))

def test_report_and_session(client):
    r=seed(client); req={'response_id':r['response_id'],'session_id':'a','title':'Sales report'}
    assert client.post('/reports',json={**req,'session_id':'b'}).status_code==404
    report=client.post('/reports',json=req);assert report.status_code==200
    url=report.json()['download_url'];assert client.get(url+'?session_id=b').status_code==404
    pdf=client.get(url+'?session_id=a');assert pdf.status_code==200
    assert '420' in PdfReader(io.BytesIO(pdf.content)).pages[0].extract_text()
    client.delete('/sessions/a');assert client.get(url+'?session_id=a').status_code==404

def test_style_variation_and_bounds(client):
    a,_,_=plan_report({},'formal serif purple landscape');b,_,_=plan_report({},'accessible large blue Letter')
    assert a.font=='serif' and a.orientation=='landscape' and a.color!=b.color
    assert b.body_size==12 and b.page_size=='Letter'
    r=seed(client);req={'response_id':r['response_id'],'session_id':'a'}
    assert client.post('/reports',json={**req,'style':{'body_size':99}}).status_code==422
    assert client.post('/reports',json={**req,'style':{'font':'../../bad'}}).status_code==422

def test_escaped_markup(client):
    r=seed(client);req={'response_id':r['response_id'],'session_id':'a','title':'<b>literal title</b>'}
    j=client.post('/reports',json=req).json();pdf=client.get(j['download_url']+'?session_id=a')
    assert '<b>literal title</b>' in PdfReader(io.BytesIO(pdf.content)).pages[0].extract_text()

def test_token(client,monkeypatch):
    monkeypatch.setenv('APP_API_TOKEN','example-test-token')
    assert client.get('/health').status_code==200
    assert client.post('/ask',json={'question':'sales'}).status_code==401
    assert client.post('/ask',json={'question':'sales'},headers={'Authorization':'Bearer example-test-token'}).status_code==200

def test_long_answer_starts_on_first_page(tmp_path):
    from task5.pdf_renderer import render_pdf
    from task5.schemas import ReportStyle
    path=tmp_path/'long.pdf'
    render_pdf(path,'Long report','Question',{'answer':'Pagination fixture content. '*600,'enough_evidence':True},ReportStyle())
    reader=PdfReader(path)
    assert len(reader.pages)>1 and len(reader.pages[0].extract_text())>800

def test_live_pipeline_preserved(monkeypatch):
    import sys,types
    monkeypatch.setenv('APP_MODE','llm')
    fake=types.ModuleType('orchestrator');fake.run_workflow=lambda question,history=None:{'answer':'delegated'}
    monkeypatch.setitem(sys.modules,'orchestrator',fake)
    assert workflow.answer('question',[])['answer']=='delegated'
