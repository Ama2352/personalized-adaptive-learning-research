"""ROOT-only explicit pointer promotion; source-prep, not run/fit authority.

Optimistic compare + atomic rename needs ROOT's sole-writer maintenance window.
No fullGate/model rerun. Never force a foreign pointer or rewrite old reports.
"""
import time
START = time.perf_counter()
from pathlib import Path
import argparse
import hashlib
import json
import os
import sys
import uuid

ROOT=Path(__file__).resolve().parents[4]
PREP=Path(__file__).resolve().parent
DIRECTORY=ROOT/'artifacts/akt/preflight'
POINTER=DIRECTORY/'gate2-current.json'
OUT=PREP/'gate03-pointer-promotion01'
OLD_SHA='7ecd8067fd3f30b658867fd5540ec331653ec4a8d6a5d1d3a0a68f932fa7690f'
PINS={
    'artifacts/akt/preflight/gate2-evidence-win-current-gate-20261109-03.json':'5a0bc5ed6fa2f0d799710f03fb17612ea0b5dbb14ce6414410f98dbfd54c85e8',
    'artifacts/akt/preflight/gate2-tests-win-current-gate-20261109-03.log':'10a1e4bbb4184439cccd6afe685566a2060f948f9c12012ee0186df8caa320d5',
    'artifacts/akt/preflight/gate2-tests-win-current-gate-20261109-03.xml':'c45ef30ce95662e4b8e2eb28f50fea69aa0fd3a8a37cda74e5b992de43a2f56f',
    'artifacts/akt/local-tests/akt-research-runner-20261108-01/win-current-gate-20261109-03-outer/result.json':'fef18bdbd45ccb9eb6a42f11da0c26bc50fc54ab4d503edbf13024562accb45e',
    'artifacts/akt/local-tests/akt-research-runner-20261108-01/windows_current_gate_packet03.ROOT.json':'7e6fe2342eb402b5ec0927ee8f1e13a5326b558ed0df71d5ae8a2c5e5c750015',
    'artifacts/akt/preflight/runtime-v2.json':'259c171fe63e39a14d9bdf42793bd854a5be73ded19a7a800a2e8a982906f1b4',
    'requirements-akt.lock.txt':'3e721fdb49543ad0888cf02a863826ebc6144c0d1dd670f2490ebcc0d69b8c0a',
}


def need(ok,reason):
    if not ok: raise ValueError(reason)


def sha(raw): return hashlib.sha256(raw).hexdigest()


def write_bytes(path,raw):
    with safe(path).open('xb') as stream:
        need(stream.write(raw)==len(raw),'short metadata write');stream.flush();os.fsync(stream.fileno())


def write(path,value):
    write_bytes(path,(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--apply',action='store_true',required=True)
    parser.add_argument('--expected-pointer-sha256',required=True)
    parser.add_argument('--expected-source-sha256',required=True)
    parser.add_argument('--sole-writer-review-reference',required=True)
    args=parser.parse_args()
    need(args.apply and args.sole_writer_review_reference.strip(),'ROOT explicit promotion/sole-writer review required')
    sys.path.insert(0,str(ROOT/'scripts/research'))
    global safe,bounded
    from windows_owned_worker import safe,bounded,entry
    entry()
    own=Path(__file__).resolve()
    need(sha(bounded(own,128*1024))==args.expected_source_sha256,'reviewed promotion controller')
    need(args.expected_pointer_sha256==OLD_SHA and sha(bounded(POINTER,128*1024))==OLD_SHA,'exact reviewed old pointer, no auto-refresh/overwrite')
    need(not OUT.exists(),'exclusive one promotion attempt, no retry')
    for name,digest in PINS.items(): need(sha(bounded(ROOT/name,4*1024**2))==digest,'actual03/runtime/lock identity:'+name)
    native=json.loads(bounded(DIRECTORY/'gate2-evidence-win-current-gate-20261109-03.json',4*1024**2))
    outer=json.loads(bounded(PREP/'win-current-gate-20261109-03-outer/result.json',4*1024**2))
    need(native['status']=='PASS' and native['test_result']==dict(passed=1418,failed=0,errors=0,skipped=0)
         and outer['status']=='ACCEPTED_WINDOWS_CPU_SOFTWARE_GATE_ONLY' and outer['run_accepted'] is True
         and outer['owned_receipt']['cleanup_accepted'] is True and outer['owned_receipt']['job_active_after_cleanup']==0
         and outer['pointer_changed'] is False and outer['errors']==[],'actual accepted fullGate03 only')
    sys.path.insert(0,str(ROOT/'src'))
    from knowledge_tracing.akt.authorization import gate2_build_hashes,preflight,require_gate2_evidence
    from knowledge_tracing.akt.config import AKTConfig
    need('torch' not in sys.modules,'metadata-only promotion')
    need(len(native['build_hashes'])==154 and gate2_build_hashes()==native['build_hashes'],'current154source freeze')
    before=bounded(POINTER,128*1024)
    safe(OUT).mkdir(exist_ok=False)
    write_bytes(OUT/'pointer-before.bytes',before)
    environment_before=dict(os.environ)
    published=False;rollback=None;errors=[];candidate=None
    result=dict(status='REJECTED_POINTER_PROMOTION',sole_writer_review_reference=args.sole_writer_review_reference,
        pointer_before_sha256=sha(before),input_sha256=PINS,authority_vi='Pointer consumption metadata only; no training/spending authority.',
        concurrency_vi='Cooperative sole-writer window required. Read/compare then atomic replace is NOT an atomic cross-process CAS.')
    raw=None
    try:
        count=int(os.environ.get('GIT_CONFIG_COUNT','0'));need(0<=count<32,'bounded local Git environment')
        os.environ[f'GIT_CONFIG_KEY_{count}']='safe.directory'
        os.environ[f'GIT_CONFIG_VALUE_{count}']=(ROOT/'artifacts/akt/dependencies/upstream').as_posix()
        os.environ['GIT_CONFIG_COUNT']=str(count+1)
        config=AKTConfig()
        result['runtime_preflight']=preflight(config,project_root=ROOT,runtime_report_path=DIRECTORY/'runtime-v2.json',lock_file=ROOT/'requirements-akt.lock.txt')
        need(result['runtime_preflight']['source']==native['source'],'fresh runtime/native source context')
        payload=dict(schema_version=1,evidence_file='gate2-evidence-win-current-gate-20261109-03.json',
            evidence_sha256=PINS['artifacts/akt/preflight/gate2-evidence-win-current-gate-20261109-03.json'],
            test_log_file='gate2-tests-win-current-gate-20261109-03.log',
            test_log_sha256=PINS['artifacts/akt/preflight/gate2-tests-win-current-gate-20261109-03.log'])
        raw=(json.dumps(payload,sort_keys=True)+'\n').encode()
        candidate=safe(DIRECTORY/f'gate2-promotion-candidate-{uuid.uuid4().hex}.tmp')
        write_bytes(candidate,raw)
        result['candidate_path']=candidate.relative_to(ROOT).as_posix();result['candidate_sha256']=sha(raw)
        result['candidate_reader']=require_gate2_evidence(config,project_root=ROOT,gate2_report=candidate,lock_file=ROOT/'requirements-akt.lock.txt')
        need(time.perf_counter()-START<20,'reserve10s for promotion validation/rollback/receipt')
        for name,digest in PINS.items(): need(sha(bounded(ROOT/name,4*1024**2))==digest,'input drift before promotion')
        need(gate2_build_hashes()==native['build_hashes'] and bounded(candidate,128*1024)==raw,'candidate/source drift')
        need(bounded(POINTER,128*1024)==before and sha(before)==args.expected_pointer_sha256,'optimistic CAS mismatch; leave foreign pointer intact')
        candidate.replace(POINTER);published=True  # Atomic rename; sole-writer assumption explicit.
        result['published_reader']=require_gate2_evidence(config,project_root=ROOT,gate2_report=POINTER,lock_file=ROOT/'requirements-akt.lock.txt')
        need(bounded(POINTER,128*1024)==raw and gate2_build_hashes()==native['build_hashes'],'post-promotion pointer/source validation')
        for name,digest in PINS.items(): need(sha(bounded(ROOT/name,4*1024**2))==digest,'post-promotion input drift')
        need(time.perf_counter()-START<30 and 'torch' not in sys.modules,'metadata-only postcheck30s')
        result['status']='PROMOTED_CURRENT_WINDOWS_CPU_SOFTWARE_GATE_ONLY'
    except BaseException as error:
        errors.append(dict(type=type(error).__name__,message=str(error)))
        if published:
            try:
                need(bounded(POINTER,128*1024)==raw,'rollback refused: current pointer is not our exact candidate')
                rollback=safe(DIRECTORY/f'gate2-promotion-rollback-{uuid.uuid4().hex}.tmp')
                write_bytes(rollback,before)
                need(bounded(POINTER,128*1024)==raw,'rollback CAS changed; no overwrite')
                rollback.replace(POINTER)
                result['rollback_accepted']=bounded(POINTER,128*1024)==before
            except BaseException as rollback_error:
                errors.append(dict(stage='conditional_own_candidate_rollback',type=type(rollback_error).__name__,message=str(rollback_error)))
    finally:
        os.environ.clear();os.environ.update(environment_before)
        after=bounded(POINTER,128*1024)
        write_bytes(OUT/'pointer-after.bytes',after)
        result.update(errors=errors,published=published,pointer_after_sha256=sha(after),environment_restored=dict(os.environ)==environment_before,
            elapsed_seconds=time.perf_counter()-START,candidate_path=None if candidate is None else str(candidate),
            candidate_remains=candidate is not None and candidate.exists(),
            scope_vi='No tests/model/nativeGate rerun. Current154/software only, no Linux/CUDA/training/realdata authority. Metadata30s cooperative; no hard transactional/crash recovery proof.')
        accepted=not errors and result['status']=='PROMOTED_CURRENT_WINDOWS_CPU_SOFTWARE_GATE_ONLY' and after==raw and result['elapsed_seconds']<30
        result['accepted']=accepted
        write(OUT/'result.json',result)
        if time.perf_counter()-START>=30:
            write(OUT/'postwrite-rejection.json',dict(status='REJECTED_POSTWRITE_BUDGET_REVIEW_CURRENT_POINTER',pointer_sha256=sha(bounded(POINTER,128*1024))))
            accepted=False
    print(json.dumps(dict(status=result['status'] if accepted else 'REJECTED_POINTER_PROMOTION',accepted=accepted,result=str(OUT/'result.json'))))
    raise SystemExit(0 if accepted else 1)


if __name__=='__main__':main()
