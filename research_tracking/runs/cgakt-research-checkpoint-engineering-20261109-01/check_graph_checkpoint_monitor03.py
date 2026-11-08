"""ROOT-only5stdlibcanaries: AST helper monitor02; không import worker/native."""
import time
START, WALL = time.perf_counter(), time.time()
import ast
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import threading
import unittest

P = Path(__file__).resolve().parent
WORKER = P/'check_graph_checkpoint_native03.py'
OUT = P/'graph-checkpoint-monitor03'
need = lambda ok,message: None if ok else (_ for _ in ()).throw(ValueError(message))
need(len(sys.argv) == 2 and not OUT.exists(), 'reviewed worker SHA/exclusive canary output')
before = hashlib.sha256(WORKER.read_bytes()).hexdigest()
need(before == sys.argv[1], 'reviewed corrected worker bytes')
OUT.mkdir()
timer = threading.Timer(4.5, lambda: os._exit(124)); timer.daemon = True; timer.start()
blocked = []
def audit(event, args):
    if event == 'import' and str(args[0]).split('.')[0] in ('torch','numpy','pandas','knowledge_tracing'):
        blocked.append(event); raise RuntimeError('stdlib-only monitor canary')
    if event == 'subprocess.Popen' or event == 'os.system' or event.startswith('os.spawn') or event.startswith('socket.'):
        blocked.append(event); raise RuntimeError('no child/network canary')
sys.addaudithook(audit)
tree = ast.parse(WORKER.read_bytes())
nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'monitor_file_size']
need(len(nodes) == 1, 'exact actual monitor helper AST')
namespace = {}
exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])), '<ACTUAL_MONITOR_HELPER_AST_ONLY>', 'exec'), namespace)
helper = namespace['monitor_file_size']


class Probe:
    def __init__(self, path, *, delete=False, error=None):
        self.path, self.name, self.delete, self.error = path, path.name, delete, error
        self.deleted_between_is_file_and_stat = False
    def is_file(self):
        value = self.path.is_file()
        if self.delete:
            need(self.path.resolve().is_relative_to(OUT.resolve()), 'owned manufactured deletion only')
            self.path.unlink(); self.deleted_between_is_file_and_stat = True
        return value
    def stat(self):
        if self.error is not None: raise self.error
        return self.path.stat()


def toy(name):
    path = OUT/name; path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as stream: stream.write(b'1234567')
    return path


class MonitorContracts(unittest.TestCase):
    def test_known_pending_disappearance_between_probe_and_stat(self):
        for name in ('state.pt.pending','metadata.json.pending','COMPLETE.json.pending'):
            # Old two-observation idiom reproduces the same ENOENT category.
            old = Probe(toy('old-'+name+'/file'),delete=True)
            with self.assertRaises(FileNotFoundError):
                if old.is_file(): old.stat()
            current = Probe(toy('current-'+name+'/'+name),delete=True)
            self.assertIsNone(helper(current))
            self.assertTrue(current.deleted_between_is_file_and_stat)
    def test_stable_regular_file_and_existing_directory(self):
        self.assertEqual(helper(Probe(toy('stable/state.pt'))), 7)
        directory = OUT/'directory'; directory.mkdir()
        self.assertIsNone(helper(Probe(directory)))
    def test_missing_nonpending_stays_error(self):
        for name in ('state.pt','metadata.json','COMPLETE.json'):
            probe = Probe(toy('final-'+name+'/'+name),delete=True)
            with self.assertRaises(FileNotFoundError): helper(probe)
            self.assertTrue(probe.deleted_between_is_file_and_stat)
    def test_unknown_pending_name_stays_error(self):
        probe = Probe(toy('unknown/arbitrary.pending'),delete=True)
        with self.assertRaises(FileNotFoundError): helper(probe)
    def test_other_errors_not_swallowed_for_known_pending(self):
        for ordinal,error in enumerate((PermissionError('explicit permission canary'),OSError(123,'explicit other OS error'))):
            with self.assertRaises(type(error)):
                helper(Probe(toy(f'error-{ordinal}/state.pt.pending'),error=error))


output = io.StringIO()
result = unittest.TextTestRunner(stream=output,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(MonitorContracts))
after = hashlib.sha256(WORKER.read_bytes()).hexdigest()
with (OUT/'stdout.log').open('x',encoding='utf-8') as stream: stream.write(output.getvalue())
accepted = result.testsRun == 5 and not result.failures and not result.errors and not result.skipped and before == after and not blocked
elapsed = max(time.perf_counter()-START,time.time()-WALL)
accepted = accepted and elapsed < 5
receipt = dict(status='ACCEPTED_5_STDLIB_MONITOR_CANARIES_NOT_NATIVE' if accepted else 'REJECTED_KEEP_ALL',
    counts=dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped)),
    worker_sha256_before=before,worker_sha256_after=after,source=WORKER.name,
    helper='AST-extracted actual monitor_file_size only; worker module body NOT executed',
    blocked_attempts=blocked,elapsed_seconds=elapsed,cap_seconds=5,
    actual_framework_imports=False,actual_nn_or_optimizer_calls=0,
    scope_vi='Deterministic owned7byte files deleted between is_file/stat. Only3knownpending names tolerateENOENT; stable/missingfinal/othererrors remainstrict. Not native checkpoint acceptance.')
with (OUT/'result.json').open('x',encoding='utf-8') as stream:
    json.dump(receipt,stream,ensure_ascii=False,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
if max(time.perf_counter()-START,time.time()-WALL) >= 5:
    with (OUT/'postwrite_rejection.json').open('x',encoding='utf-8') as stream: json.dump(dict(status='REJECTED_CANARY_POSTWRITE_TIME'),stream)
    accepted = False
timer.cancel()
print(json.dumps(dict(status=receipt['status'] if accepted else 'REJECTED_KEEP_ALL',counts=receipt['counts'],elapsed_seconds=max(time.perf_counter()-START,time.time()-WALL))))
raise SystemExit(0 if accepted else 1)
