"""Áp dụng sáu fixture đã review và tạo runner91ca, chưa chạy tests."""
import hashlib
import json
from pathlib import Path
import pprint
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
assert Path(sys.prefix).resolve() == ROOT / '.venv'
candidate = PREP / 'test_paper1_concept_local_invariance_candidate01.py'
raw = candidate.read_bytes()
assert hashlib.sha256(raw).hexdigest() == 'dfa6b07572a76fcf53e48d7815f957bda40c00755ea44cb3d5fc705f2767104f'
text = raw.decode('utf-8').replace('Fixtures dựng tay cho mệnh đề có điều kiện, chưa chạy test hoặc matrix.',
    'Fixtures dựng tay cho bất biến concept-local có điều kiện và các ranh giới.')
text = text.replace('A nonempty comparison, not vacuous disjoint prefixes.',
    'Prefix chung có dữ liệu, không chỉ so hai prefix rỗng.')
target = ROOT / 'tests/paper1_pdf/test_concept_local_invariance.py'
runner = PREP / 'run_paper1_invariance_tests01.py'
assert not target.exists() and not runner.exists()
compile(text, str(target), 'exec')
old_runner = (PREP / 'run_paper1_seeded_tests01.py').read_text(encoding='utf-8')
start = old_runner.index('PINS = {') + len('PINS = ')
end = old_runner.index('\n}', start) + 2
import ast
pins = ast.literal_eval(old_runner[start:end])
pins[target.relative_to(ROOT).as_posix()] = hashlib.sha256(text.encode('utf-8')).hexdigest()
for name, pin in pins.items():
    if name != target.relative_to(ROOT).as_posix():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == pin
runner_source = '''"""Root kiểm91ca Paper1 bằng source mới, không model/data framework."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

START = time.perf_counter()
ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
OUTPUT = PREP / 'paper1-invariance-tests01'
PINS = __PINS__


def hashes():
    return {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in PINS}


assert Path(sys.prefix).resolve() == ROOT/'.venv' and sys.dont_write_bytecode
assert hashes() == PINS and not OUTPUT.exists()
OUTPUT.mkdir()
temporary = OUTPUT/'temporary'
temporary.mkdir()
script = """import json,sys
denied=[]
def audit(kind,args):
    if kind=='import' and str(args[0]).split('.')[0] in ('torch','numpy','pandas','scipy','sklearn','modal','boto3'):
        denied.append(str(args[0])); raise RuntimeError('Không import framework trong pure fixtures')
    if kind in ('subprocess.Popen','os.system','socket.__new__'):
        denied.append(kind); raise RuntimeError('Không tạo process/network trong pure fixtures')
sys.addaudithook(audit)
import unittest
def leaves(suite):
    for item in suite:
        if isinstance(item,unittest.TestSuite):yield from leaves(item)
        else:yield item.id()
suite=unittest.defaultTestLoader.discover('tests/paper1_pdf',pattern='test_*.py')
collected=list(leaves(suite))
started=[];completed=[]
class Result(unittest.TextTestResult):
    def startTest(self,test):
        started.append(test.id()); super().startTest(test)
    def stopTest(self,test):
        completed.append(test.id()); super().stopTest(test)
result=unittest.TextTestRunner(verbosity=2,resultclass=Result).run(suite)
new_ids=[name for name in collected if name.startswith('test_concept_local_invariance.')]
cold=not any(name in sys.modules for name in ('torch','numpy','pandas'))
counts=dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),
    expected_failures=len(result.expectedFailures),unexpected_successes=len(result.unexpectedSuccesses))
accepted=(counts==dict(tests=91,failures=0,errors=0,skipped=0,expected_failures=0,unexpected_successes=0)
    and len(new_ids)==6 and len(set(collected))==91 and collected==started==completed and cold and not denied)
print(json.dumps(dict(accepted=accepted,counts=counts,collected_ids=collected,started_ids=started,completed_ids=completed,
    new_ids=new_ids,scientific_modules_absent=cold,denied=denied,pycache_prefix=sys.pycache_prefix)))
raise SystemExit(0 if accepted else 1)
"""
environment=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(ROOT/'src'),
    PYTHONPYCACHEPREFIX=str(temporary/'fresh-bytecode'),TEMP=str(temporary),TMP=str(temporary),
    CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2')
command=[sys.executable,'-B','-c',script]
remaining=30-(time.perf_counter()-START)-2
assert remaining>0
timed_out=False
try:
    child=subprocess.run(command,cwd=ROOT,env=environment,capture_output=True,timeout=min(25,remaining))
    stdout,stderr,returncode=child.stdout,child.stderr,child.returncode
except subprocess.TimeoutExpired as error:
    stdout,stderr,returncode=error.stdout or b'',error.stderr or b'',None
    timed_out=True
(OUTPUT/'stdout.log').write_bytes(stdout)
(OUTPUT/'stderr.log').write_bytes(stderr)
observed=json.loads(stdout.decode('utf-8').splitlines()[-1]) if stdout else None
after=hashes()
elapsed=time.perf_counter()-START
accepted=returncode==0 and not timed_out and elapsed<30 and observed is not None and observed['accepted'] and after==PINS
result=dict(status='ACCEPTED91_PAPER1_CASES_WITH6_LOCAL_INVARIANCE_FIXTURES' if accepted else 'REJECTED_KEEP_ALL',
    counts=observed,returncode=returncode,timed_out=timed_out,elapsed_seconds=elapsed,whole_cap_seconds=30,
    source_before=PINS,source_after=after,command=command,new_fixture_methods=6,
    static_new_fixture_upper_bounds=dict(episode_calls=13,feedback_horizon_sum=464,extra_ready_only_controllers=1),
    scope_vi='Hồi quy85ca cũ và6fixture dựng tay. Không matrix hoặc suy phạm vi ngoài điều kiện mệnh đề.')
(OUTPUT/'result.json').write_bytes((json.dumps(result,ensure_ascii=False,indent=2)+'\\n').encode('utf-8'))
print(json.dumps(dict(status=result['status'],tests=None if observed is None else observed['counts'],elapsed_seconds=elapsed)))
raise SystemExit(0 if accepted else 1)
'''.replace('__PINS__', pprint.pformat(pins, sort_dicts=False, width=100))
compile(runner_source, str(runner), 'exec')
with target.open('xb') as stream:
    stream.write(text.encode('utf-8'))
with runner.open('xb') as stream:
    stream.write(runner_source.encode('utf-8'))
proof = dict(status='APPLIED_NEW_FIXTURE_FILE_RUNNER_PREPARED_NOT_EXECUTED',
    candidate_sha256=hashlib.sha256(raw).hexdigest(),
    test_path=target.relative_to(ROOT).as_posix(), test_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
    runner_path=runner.relative_to(ROOT).as_posix(), runner_sha256=hashlib.sha256(runner.read_bytes()).hexdigest(),
    source_pins=len(pins), expected_tests=91, new_tests=6)
with (PREP / 'paper1_invariance_test_apply01.json').open('x', encoding='utf-8') as stream:
    json.dump(proof, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps(proof))
