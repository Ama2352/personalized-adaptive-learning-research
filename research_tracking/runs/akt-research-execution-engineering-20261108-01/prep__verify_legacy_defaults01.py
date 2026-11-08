"""Golden AST/asdict defaults only; no validation/model/Git/process call."""
import time
START=time.monotonic();WALL=time.time()
import ast
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys
import types

ROOT=Path(__file__).resolve().parents[4]
PREP=Path(__file__).resolve().parent
current_path=ROOT/'src/knowledge_tracing/akt/config.py'
before_path=PREP/'config.py.before'
before_raw=before_path.read_bytes();current_raw=current_path.read_bytes()
sha=lambda raw:hashlib.sha256(raw).hexdigest()
sys.path.insert(0,str(ROOT/'src'))
from knowledge_tracing.akt import config as current
old=types.ModuleType('legacy_defaults_config_snapshot')
old.__file__=str(current_path)  # Exact historical source location preserves PROJECT_ROOT default.
sys.modules[old.__name__]=old
exec(compile(before_raw,str(before_path),'exec'),old.__dict__)
serialize=lambda value:json.dumps(asdict(value),default=str,sort_keys=True,allow_nan=False)
old_defaults=serialize(old.AKTConfig());new_defaults=serialize(current.AKTConfig())
node=lambda raw:next(x for x in ast.parse(raw).body if isinstance(x,ast.ClassDef) and x.name=='AKTConfig')
assert ast.dump(node(before_raw))==ast.dump(node(current_raw))
assert old_defaults==new_defaults
assert sha(before_path.read_bytes())==sha(before_raw) and sha(current_path.read_bytes())==sha(current_raw)
assert 'torch' not in sys.modules
elapsed=max(time.monotonic()-START,time.time()-WALL)
prior=json.loads((PREP/'trial02/receipt.json').read_bytes())['cumulative_seconds']
assert elapsed+prior<=30
result=dict(status='PASS_AST_AND_SERIALIZED_DEFAULTS_IDENTICAL',config_before_sha256=sha(before_raw),
    config_after_sha256=sha(current_raw),default_asdict_sha256=sha(old_defaults.encode()),
    default_asdict=json.loads(old_defaults),helper_elapsed_seconds=elapsed,cumulative_seconds=prior+elapsed,
    cap_seconds=30,neural_calls=0,optimizer_updates=0,subprocess_calls=0,
    scope='Direct pure source/default proof; not another61test run or actual runtime preflight')
(PREP/'legacy-defaults01.json').open('x',encoding='utf-8').write(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='default_asdict'}))
