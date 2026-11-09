"""Root kiểm91ca Paper1 bằng source mới, không model/data framework."""
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
PINS = {'src/knowledge_tracing/paper1_pdf/__init__.py': '0a9e0faa63680643c3526ce13135de2c033f105d82bf5ea8e7a55afdc2df7df7',
 'src/knowledge_tracing/paper1_pdf/simulator.py': 'b73057bc0523742fe9f8d84f543e305652c032973facbd327437331affb3d37f',
 'src/knowledge_tracing/paper1_pdf/domain.py': 'c37e32420c90f98289b9e21c2e6ea9197324f77a2452b7faae79f8c60985fb18',
 'src/knowledge_tracing/paper1_pdf/episode.py': 'e01fc94656e206101a6ab6dfc960eb24ac331a677f3711c2b4561fbcd840b471',
 'src/knowledge_tracing/paper1_pdf/seeded_episode.py': '7c7ac305cd49fd79f5768173198705be7fa32586114acf5871950c7540dda1b2',
 'tests/paper1_pdf/test_simulator.py': '0810c04847a0461bcb2ed8ddf5cb17fda13ab90dca1709adc7bc16ee847c8a03',
 'tests/paper1_pdf/test_domain.py': '5443ff36d437c4ed9a758089a0114e6a5b4da1396a137ec5b7ec5e4b16e9afdb',
 'tests/paper1_pdf/test_reentry_mechanism.py': '365b062098ea2edcb5ac320b469d593024fd577a7801c7a4b9fd35eff7b86074',
 'tests/paper1_pdf/test_episode.py': 'd0bf6e052d9e2618b0b2d3ecf729164da68d99fc49a42e4c6dc0eadf6b4db1c0',
 'tests/paper1_pdf/test_seeded_episode.py': 'f97674bc764988271c091a00560bf31f2afba2f951b72819a150ae64a83b48e2',
 'tests/paper1_pdf/test_concept_local_invariance.py': 'e38a72290e51b2e9b9bd418829bbe2344b85604ce3f6e8ebad5f6bd845a70780'}


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
(OUTPUT/'result.json').write_bytes((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
print(json.dumps(dict(status=result['status'],tests=None if observed is None else observed['counts'],elapsed_seconds=elapsed)))
raise SystemExit(0 if accepted else 1)
