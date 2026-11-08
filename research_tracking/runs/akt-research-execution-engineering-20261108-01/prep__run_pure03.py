"""ONE pure BATCH2 run;30s cumulative, no actual native preflight/model."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import time
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[4]
PREP=Path(__file__).resolve().parent
INPUTS=['src/knowledge_tracing/akt/'+n for n in ('config.py','research_execution.py','authorization.py','provenance.py')]
INPUTS+=['src/knowledge_tracing/simulator_research_collection.py','tests/akt/test_provenance.py','src/knowledge_tracing/simulator_bridge.py','src/knowledge_tracing/simulator_data.py',
    'src/knowledge_tracing/simulator_research_data.py','tests/akt/test_research_execution.py',
    'docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md',
    str((PREP/'CORPUS_SCHEMA_V1.json').relative_to(ROOT)),str((PREP/'config.py.before').relative_to(ROOT))]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    trial=PREP/'trial03';trial.mkdir()
    before={n:sha(ROOT/n) for n in INPUTS}
    for i,n in enumerate(INPUTS):(trial/f'{i:02}-{Path(n).name}.before').write_bytes((ROOT/n).read_bytes())
    command=[str(ROOT/'.venv/Scripts/python.exe'),'-I','-B','-c',
        "import sys;sys.path.insert(0,'src');import pytest;raise SystemExit(pytest.main(sys.argv[1:]))",
        'tests/akt/test_research_execution.py','tests/akt/test_provenance.py::test_config_rejects_graph_holdout_and_protected_output','tests/akt/test_provenance.py::test_phase_and_source_are_explicit','tests/akt/test_provenance.py::test_readiness_output_has_its_own_approved_directory','tests/akt/test_provenance.py::test_provisional_training_and_resource_settings_are_explicit','tests/akt/test_provenance.py::test_completed_run_cannot_be_overwritten','tests/akt/test_provenance.py::test_spoofed_project_root_cannot_authorize_a_protected_output','-q','-p','no:cacheprovider','--basetemp='+str(trial/'tmp'),
        '--junitxml='+str(trial/'junit.xml')]
    env=dict(os.environ,PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',
             OPENBLAS_NUM_THREADS='2',CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='')
    started=time.monotonic();wall=time.time();code=None;error=None
    with (trial/'stdout.log').open('xb') as out,(trial/'stderr.log').open('xb') as err:
        try:code=subprocess.run(command,cwd=ROOT,env=env,stdout=out,stderr=err,timeout=44).returncode
        except BaseException as exc:error=type(exc).__name__+': '+str(exc)
    elapsed=max(time.monotonic()-started,time.time()-wall)
    after={n:sha(ROOT/n) for n in INPUTS}
    for i,n in enumerate(INPUTS):(trial/f'{i:02}-{Path(n).name}.after').write_bytes((ROOT/n).read_bytes())
    counts=ET.parse(trial/'junit.xml').getroot().find('testsuite').attrib if (trial/'junit.xml').exists() else None
    value=dict(status='PASS' if code==0 and error is None and elapsed+13.623352999941377<=60 and before==after else 'FAILED_OR_RESOURCE_REJECTED',
        exit_code=code,error=error,controller_elapsed_seconds=elapsed,cumulative_seconds=elapsed+13.623352999941377,cap_seconds=60,
        command=command,counts=counts,source_sha256_before=before,source_sha256_after=after,
        native_runtime_gate='EXPLICIT_UNIT_MOCKS_NOT_ACTUAL_READY',inner_subprocess_calls=0,
        model_calls=0,optimizer_updates=0,torch_imports=0,corpus_generated=False,
        metadata_fixture_jsonl='intentionally unparsed bytes, not a valid research corpus',
        actual_environment_or_corpus_mutation=False,prior_cumulative_seconds=13.623352999941377,budget_revision='Root approved30to60 cumulative for critical restartable plan/provenance +fullrevisedguard +purelegacyconfig; notreset')
    (trial/'receipt.json').open('x',encoding='utf-8').write(json.dumps(value,indent=2)+'\n')
    print(json.dumps(value))
    return 0 if value['status']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
