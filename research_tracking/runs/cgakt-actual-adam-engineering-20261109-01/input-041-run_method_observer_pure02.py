"""ROOT stdlib-only5s observer canary; không model/data/native/GPU."""
import time
START=time.perf_counter()
from pathlib import Path
import hashlib
import json
import subprocess
import sys
P=Path(__file__).resolve().parent;ROOT=Path(__file__).resolve().parents[4]
assert Path(sys.prefix).resolve()==ROOT/'.venv'
pins={'method_patch_observer02.py':'57a762f20e7147f7195ee6538fecdf960cd83d556a6ac4989656e2b7c1fed42b',
      'check_method_patch_observer02.py':'fc09c7e2321215f376aba743adc91a87187f9556328c2863c474205b517610bf'}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert all(sha(P/n)==h for n,h in pins.items())
out=P/'graph10-observer-pure02';out.mkdir()
command=[sys.executable,'-B',str(P/'check_method_patch_observer02.py')]
with (out/'stdout.log').open('xb') as stdout,(out/'stderr.log').open('xb') as stderr:
    result=subprocess.run(command,cwd=ROOT,stdout=stdout,stderr=stderr,timeout=max(.1,4-(time.perf_counter()-START)))
actual=json.loads((out/'stdout.log').read_bytes())
after={n:sha(P/n) for n in pins}
accepted=result.returncode==0 and after==pins and actual==dict(kind='STDLIB_OBSERVER_ONLY_NOT_NATIVE',tests=5,failures=0,errors=0,skipped=0) and time.perf_counter()-START<5
receipt=dict(status='ACCEPTED_FIVE_STDLIB_METHOD_OBSERVER_CASES_NOT_NATIVE' if accepted else 'REJECTED_KEEP_ALL',
    returncode=result.returncode,actual=actual,source_before=pins,source_after=after,command=command,
    seconds=time.perf_counter()-START,whole_cap_seconds=5,charge_within_new_graph10_90_seconds=5,
    output_sha256={n:sha(out/n) for n in ('stdout.log','stderr.log')},scope_vi='5tinyclass inheritance fixtures, khôngTorch/data/model/optimizer/GPU/network. Regular subprocess, no descendants inreviewed source, not hard RAM quota.')
with (out/'result.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(receipt,f,ensure_ascii=False,indent=2);f.write('\n')
assert time.perf_counter()-START<5
print(json.dumps(dict(status=receipt['status'],seconds=time.perf_counter()-START,receipt_sha256=sha(out/'result.json'))))
raise SystemExit(0 if accepted else 1)
