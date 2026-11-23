"""Record real offline regression results and selected package/model metadata."""
from datetime import datetime, timezone
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

root=Path(__file__).resolve().parent.parent
out=root/'evidence';out.mkdir(exist_ok=True)
env={**os.environ,'OFFLINE_TESTS':'1'}
command=[sys.executable,'-m','pytest','tests','tests_task5','-q']
r=subprocess.run(command,cwd=root,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace')
(out/'pytest_results.txt').write_text('$ python -m pytest tests tests_task5 -q\nOFFLINE_TESTS=1\n\n'+r.stdout+r.stderr+f'\nExit code: {r.returncode}\n',encoding='utf-8')
packages=['fastapi','uvicorn','httpx','pydantic','chromadb','fastembed','openai','langchain-text-splitters','faster-whisper','rapidocr-onnxruntime','reportlab','pytest','pypdf','Pillow','numpy']
info={'timestamp_utc':datetime.now(timezone.utc).isoformat(),'python':platform.python_version(),
      'baseline_commit':'b98189b907dfeb093f65ae4faa85c81a9aea781c','pytest_exit_code':r.returncode,
      'test_mode':'offline: embedding/reranking and external LLM responses mocked by baseline test harness; adapter contracts mocked where stated',
      'live_model_evidence':'live_demo.json contains real OCR and speech recognition with extractive answers',
      'external_llm_success_verified':False,'docker_image_built':False,'cloud_deployed':False,
      'browser_microphone_tested':False,'packages':{p:metadata.version(p) for p in packages}}
if r.returncode==0:
    from fastembed import TextEmbedding
    from fastembed.rerank.cross_encoder import TextCrossEncoder
    embed_names=[m['model'] for m in TextEmbedding.list_supported_models()]
    rerank_names=[m['model'] for m in TextCrossEncoder.list_supported_models()]
    info['configured_models_registered']={
       'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2':'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2' in embed_names,
       'Xenova/ms-marco-MiniLM-L-6-v2':'Xenova/ms-marco-MiniLM-L-6-v2' in rerank_names}
(out/'application_verification.json').write_text(json.dumps(info,indent=2),encoding='utf-8')
print(r.stdout)
raise SystemExit(r.returncode)
