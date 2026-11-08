"""Local mock controller; tất cả elapsed của trial trước vẫn tính trong cap15s."""
import ast
import contextlib
import hashlib
import json
from pathlib import Path
import time
import traceback

w = Path(__file__).resolve().parent
r = w/'mock-trial03'; r.mkdir(exist_ok=False)
files = [w/'gpu10_cold_bootstrap02.py', w/'test_bootstrap02.py']
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
prior = json.loads((w/'mock-trial02/receipt.json').read_text())['cumulative_controller_seconds']
assert prior < 15
before = {p.name:sha(p) for p in files}
for p in files:
    (r/(p.name+'.before')).write_bytes(p.read_bytes()); ast.parse(p.read_bytes())
start = time.monotonic(); wall = time.time(); code = 1
with (r/'stdout.log').open('x',encoding='utf-8') as out, (r/'stderr.log').open('x',encoding='utf-8') as err, contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
    try: exec(compile(files[1].read_bytes(),str(files[1]),'exec'), {'__name__':'__main__','__file__':str(files[1])})
    except SystemExit as error: code = error.code
    except BaseException: traceback.print_exc()
elapsed = time.monotonic()-start; wall_elapsed = time.time()-wall
after = {p.name:sha(p) for p in files}
for p in files: (r/(p.name+'.after')).write_bytes(p.read_bytes())
summary = json.loads((r/'stdout.log').read_text().strip().splitlines()[-1]) if (r/'stdout.log').read_text().strip() else {}
old = json.loads((w/'revision02-input-inventory.json').read_text())
old_after = {name:sha(w/name) for name in old}
receipt = dict(status='PASS' if code==0 and prior+elapsed<=15 and prior+wall_elapsed<=15 and before==after and old==old_after else 'FAILED',
    exit_code=code,controller_elapsed_seconds=elapsed,wall_elapsed_seconds=wall_elapsed,
    prior_controller_seconds=prior,cumulative_controller_seconds=prior+elapsed,cumulative_budget_seconds=15,
    source_before=before,source_after=after,old_frozen_inputs_before=old,old_frozen_inputs_after=old_after,
    summary=summary,scope='Actual source AST fragments + virtual mocks only; zero bootstrap/venv/stage Popen/pip/device/network',
    command='.venv/Scripts/python.exe -I -S -B '+str(Path(__file__).resolve()),
    logs={p.name:sha(p) for p in (r/'stdout.log',r/'stderr.log')})
(r/'receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps(receipt))
raise SystemExit(0 if receipt['status']=='PASS' else 1)
