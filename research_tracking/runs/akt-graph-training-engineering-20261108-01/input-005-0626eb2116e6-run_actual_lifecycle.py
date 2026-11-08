"""One reviewed local CPU batch, cumulative60s/4actualsteps, all failures retained."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time,xml.etree.ElementTree as ET

r=Path.cwd();prep=Path(__file__).resolve().parent
assert Path(sys.prefix).resolve()==r/'.venv'
previous=sorted(prep.glob('actual*/receipt.json'))
assert len(previous)==len(list(prep.glob('actual[0-9][0-9]'))),'orphan attempt requires audit, not retry'
spent=sum(json.loads(p.read_text())['controller_seconds'] for p in previous)
remaining=60-spent
assert remaining>5
attempt=prep/f'actual{len(previous)+1:02d}';attempt.mkdir(exist_ok=False)
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=list((r/'src/knowledge_tracing/akt').glob('*.py'))+[r/f for f in (
    'src/knowledge_tracing/graph_context.py','src/knowledge_tracing/graph_augmentation.py',
    'tests/akt/test_graph_training.py','tests/akt/test_graph_lifecycle.py',
    'tests/akt/test_simulator_engineering.py')]
before={p.relative_to(r).as_posix():h(p) for p in files}
assert before['src/knowledge_tracing/akt/graph_training.py']=='91ae634a33b74d7fbd26abf6c08934f1329488246610e40c4c903ceffecd92f4'
assert before['src/knowledge_tracing/akt/simulator_engineering.py']=='abeff620df572bb1438dfa681c0fa4f322a2a7416580b3777fb7abd12f8704fb'
(attempt/'source_before.json').write_text(json.dumps(before,indent=2)+'\n',encoding='utf-8')
for f in ('src/knowledge_tracing/akt/graph_training.py','src/knowledge_tracing/akt/simulator_engineering.py',
          'src/knowledge_tracing/akt/training.py','tests/akt/test_graph_lifecycle.py'):
    (attempt/Path(f).name).write_bytes((r/f).read_bytes())
for f in ('actual_child.py','run_actual_lifecycle.py'):(attempt/f).write_bytes((prep/f).read_bytes())
env=dict(os.environ,PYTHONPATH=str(r/'src'),CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='',
    OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1',
    KLTN_GRAPH_ATTEMPT_ID=attempt.name)
count=int(env.get('GIT_CONFIG_COUNT','0'))
for p in (r,r/'artifacts/akt/dependencies/upstream'):
    env[f'GIT_CONFIG_KEY_{count}']='safe.directory';env[f'GIT_CONFIG_VALUE_{count}']=p.as_posix();count+=1
env['GIT_CONFIG_COUNT']=str(count)
cmd=[str(r/'.venv/Scripts/python.exe'),str(prep/'actual_child.py'),'-q',
    'tests/akt/test_simulator_engineering.py','tests/akt/test_graph_lifecycle.py',
    '-o','cache_dir='+str(attempt/'cache'),'--junitxml='+str(attempt/'pytest.xml')]
prior_dirs=set((r/'artifacts/akt/synthetic').glob('*'))
start=time.perf_counter();wall=time.time();process=None;status='FAILED'
try:
    with (attempt/'stdout.log').open('xb') as stdout,(attempt/'stderr.log').open('xb') as stderr:
        process=subprocess.Popen(cmd,cwd=r,env=env,stdout=stdout,stderr=stderr)
        try:process.wait(timeout=remaining-3)
        except subprocess.TimeoutExpired:
            status='REJECTED_CUMULATIVE_RESOURCE_BOUND';process.kill();process.wait(timeout=2)
    suites=list(ET.parse(attempt/'pytest.xml').getroot().iter('testsuite')) if (attempt/'pytest.xml').exists() else []
    counts={k:sum(int(s.get(k,0)) for s in suites) for k in ('tests','failures','errors','skipped')}
    if process.returncode==0 and counts['tests'] and not any(counts[k] for k in ('failures','errors','skipped')):
        status='PASS_ACTUAL_BASE_AND_GRAPH_ENGINEERING_LIFECYCLE'
finally:
    if process is not None and process.poll() is None:process.kill();process.wait(timeout=2)
    after={p.relative_to(r).as_posix():h(p) for p in files}
    elapsed=time.perf_counter()-start;wall_elapsed=time.time()-wall
    if after!=before:status='SOURCE_DRIFT'
    if not 0<=elapsed+spent<=60 or not 0<=wall_elapsed+spent<=60:status='REJECTED_CUMULATIVE_RESOURCE_BOUND'
    ledger=prep/'actual_optimizer_events.jsonl'
    events=[json.loads(line) for line in ledger.read_text().splitlines()] if ledger.exists() else []
    reservations=sum(e['event']=='optimizer_reservation' for e in events)
    body_returns=sum(e['event']=='optimizer_body_returned' for e in events)
    if reservations>4:status='REJECTED_OPTIMIZER_CAP'
    if status.startswith('PASS_') and (reservations!=4 or body_returns!=4):status='UNEXPECTED_OPTIMIZER_ACCOUNTING'
    created=sorted(set((r/'artifacts/akt/synthetic').glob('*'))-prior_dirs)
    receipt=dict(status=status,counts=locals().get('counts'),command=cmd,source_before=before,source_after=after,
        controller_seconds=elapsed,wall_seconds=wall_elapsed,previous_seconds=spent,cumulative_seconds=elapsed+spent,
        cumulative_cap_seconds=60,optimizer_cap=4,optimizer_reservations=reservations,optimizer_body_returns=body_returns,
        child_reaped=process is None or process.poll() is not None,
        created_run_dirs=[p.relative_to(r).as_posix() for p in created],ledger_sha256=h(ledger) if ledger.exists() else None,
        scope='Handmade CPU toy only; no realdata/Holdout/CUDA/cloud; no fitted research model or method adoption')
    (attempt/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k not in ('source_before','source_after','command')}))
raise SystemExit(0 if status.startswith('PASS_') else 1)
