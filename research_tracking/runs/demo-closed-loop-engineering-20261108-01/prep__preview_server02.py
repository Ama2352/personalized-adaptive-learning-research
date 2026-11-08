"""Bounded loopback-only UI QA; no model/research execution."""
from pathlib import Path
import sys,json,time,os,hashlib
ROOT=Path.cwd().resolve();assert Path(sys.prefix).resolve()==ROOT/'.venv'
sys.path.insert(0,str(ROOT))
from src.research_demo.server import make_server
PREP=ROOT/'artifacts/akt/local-tests/parallel-demo-20261108-01/c14-preparation'
START=time.perf_counter();stop=PREP/'preview-stop02';assert not stop.exists()
plan=json.loads((PREP/'test_plan01.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={p:sha(ROOT/p) for p in plan['source_sha256']};assert before==plan['source_sha256']
server=make_server(0);server.timeout=.2
receipt={'status':'LISTENING_LOOPBACK_UI_QA_MAX180_SECONDS','pid':os.getpid(),'url':'http://127.0.0.1:'+str(server.server_port)+'/','max_seconds':180,'source_sha256':before,'model_optimizer_research_replay_calls':0}
(PREP/'preview-listener02.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(receipt,ensure_ascii=False),flush=True)
try:
 while not stop.exists() and time.perf_counter()-START<180:server.handle_request()
finally:
 server.server_close();after={p:sha(ROOT/p) for p in before}
 (PREP/'preview-shutdown02.json').write_text(json.dumps({'status':'CLOSED_LOOPBACK_PREVIEW','elapsed_seconds':time.perf_counter()-START,'stop_marker':stop.exists(),'source_unchanged':before==after,'model_optimizer_research_replay_calls':0},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
