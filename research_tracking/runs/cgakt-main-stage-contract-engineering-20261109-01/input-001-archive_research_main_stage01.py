"""ROOT-only metadata dry/close GRAPH18; no test/model execution or data reads."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import sys

R=Path(__file__).resolve().parents[4]
P=Path(__file__).resolve().parent
RUN_ID='cgakt-main-stage-contract-engineering-20261109-01'
CANDIDATE=P/'cgakt_main_stage_contract_20261109.candidate.md'
CANONICAL=R/'research_tracking/reports/cgakt_main_stage_contract_20261109.md'
REPORT_SHA='fb1994ee76bc1616c542ed4e6e04cfb637a661c15bc9d142572c132ac1bbd11e'
PINS={
    'src/knowledge_tracing/akt/research_main_stage.py':'77b7dbfd75f715f3a4179286cd742780581151dc39c39748213c9c55c25b13c1',
    'tests/akt/test_research_main_stage.py':'68f1e02921729c3de9595528302a1bd07513fbaf926871a4308048c72cefa851',
    'artifacts/akt/local-tests/akt-research-runner-20261108-01/check_research_main_stage01.py':'68c8f12a5e496e61ac8ae49bbf4726c5ac2772754531073a59372d6e7429983a',
    'artifacts/akt/local-tests/akt-research-runner-20261108-01/research_main_stage_pure_packet01.json':'31611f46bfd3ab0e09dd9aa15e47f7b63ae693f307f911acfdaa7049d2f7bdd3',
}


def need(ok,message):
    if not ok:raise ValueError(message)


def sha(raw):return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')


def safe(path,existing=True):
    path=Path(path)
    need(path.is_absolute() and '..' not in path.parts and path.is_relative_to(R),'fixed project path')
    cursor=R
    for part in (None,*path.relative_to(R).parts):
        if part is not None:cursor/=part
        need(not cursor.is_symlink() and not getattr(cursor,'is_junction',lambda:False)(),'alias rejected')
    need(path.resolve().is_relative_to(R.resolve()),'physical project path')
    if existing:need(path.is_file(),'regular file required')
    return path


def gather(report):
    payloads={}
    def read(path):
        path=safe(path)
        if path not in payloads:
            need(path.stat().st_size<=262144,'small artifact cap')
            raw=path.read_bytes();need(len(raw)<=262144,'bounded readback')
            payloads[path]=raw;need(sum(map(len,payloads.values()))<=2*1024**2,'compact total cap')
        return payloads[path]
    load=lambda path:json.loads(read(path))
    for name,digest in PINS.items():need(sha(read(R/name))==digest,'source/controller/packet drift')
    need(report in (CANDIDATE,CANONICAL) and sha(read(report))==REPORT_SHA,'reviewed report bytes')
    packet=load(P/'research_main_stage_pure_packet01.json')
    capture=P/'research-main-stage-pure-capture01';owned_dir=P/'research-main-stage-pure-owned01'
    final=load(capture/'final.json');worker=load(capture/'worker-result.json');canary=load(capture/'cold-canary.json')
    owned=load(owned_dir/'receipt.json')
    need(sha(read(capture/'final.json'))=='6720977ab7d863a4aebef36b5c78e4066c8ef406c99862496503724f65694ed4'
         and sha(read(capture/'worker-result.json'))=='943a5c1623c0c79d3298fffe855dc4509d1e0589479022bb61dc682cf3072ab5','actual receipt identities')
    counts=dict(tests=14,failures=0,errors=0,skipped=0)
    need(final['status']=='ACCEPTED_GRAPH18_14_PURE_STAGE_CONTRACT_CASES_ONLY' and final['errors']==[]
         and worker['status']=='ACCEPTED_14_PURE_MAIN_STAGE_PENDING_OUTER' and worker['original_error'] is None
         and final['counts']==worker['counts']==counts,'actual14unittest verdict')
    sources,runtimes=packet['source_pins'],packet['runtime_pins']
    need(len(sources)==14 and len(runtimes)==11
         and sources==final['source_before']==final['source_after']==worker['source_before']==worker['source_after']
         and runtimes==final['runtime_before']==final['runtime_after']==worker['runtime_before']==worker['runtime_after'],
         'source14/runtime11 before/after')
    need(final['allocation_sha256']==worker['allocation_sha256']==sha(read(P/'research_main_stage_pure_packet01.json')),
         'actual packet binding')
    need(owned['accepted'] and owned['cleanup_accepted'] and owned['job_active_after_cleanup']==0
         and owned['actual_worker_in_job_before_GO'] and owned['popen_handle_closed'] and owned['returncode']==0
         and owned['errors']==[],'actual owned Job cleanup')
    need(worker['cold_import']==canary and canary['status']=='STDLIB_MAIN_STAGE_COLD_IMPORT_ONLY'
         and canary['status_label']=='NO_EXECUTION_AUTHORITY' and canary['artifact_bytes_verified'] is False
         and canary['external_freeze_authority'] is False and worker['cached_real_class_identity']
         and worker['denied_attempts']==[] and worker['scientific_modules_present']==[]
         and worker['environment_restored'],'cold real modules and no scientific imports/grant')
    need(final['elapsed_before_receipt_seconds']<30 and worker['elapsed_worker_seconds']<27
         and final['cap_seconds']==30 and final['cleanup_reserve_seconds']==2,'actual whole/cleanup budget')
    need(sha(read(owned_dir/'receipt.json'))==final['owned_receipt_sha256'],'outer/owned receipt binding')
    for name,digest in final['output_sha256'].items():
        need(name in ('before.json','cold-canary.json','worker-result.json') and sha(read(capture/name))==digest,'capture byte binding')
    for name,digest in owned['output_sha256'].items():
        need(name in ('stdout.log','stderr.log') and sha(read(owned_dir/name))==digest,'owned stdout/stderr binding')
    stderr=read(owned_dir/'stderr.log').decode('utf-8')
    matches=re.findall(r'(?m)^Ran (\d+) tests? in ([0-9.]+)s\s*$',stderr)
    need(len(matches)==1 and int(matches[0][0])==14 and re.search(r'(?m)^OK\s*$',stderr)
         and '(skipped=' not in stderr,'raw unittest14complete0FES')
    for name in ('before.json','cold-canary.json','worker-result.json','final.json'):read(capture/name)
    for name in ('GO.json','launch.json','ready.json','receipt.json','stdout.log','stderr.log'):read(owned_dir/name)
    before=P/'main-stage-before-epoch-validation01';snapshot=load(before/'inventory.json')
    need(snapshot['actual_test_runs']==0 and len(snapshot['copies'])==2,'static-before-first-execution correction')
    for row in snapshot['copies']:
        need(sha(read(before/row['snapshot']))==row['sha256_before_copy']==row['sha256_after_copy']
             ==row['source_sha256_after_copy'],'before source snapshot bytes')
    read(Path(__file__).resolve())
    rows=[dict(source=path.relative_to(R).as_posix(),bytes=len(raw),sha256_before_copy=sha(raw),
               archived_as=f'input-{ordinal:03d}-'+path.name)
          for ordinal,(path,raw) in enumerate(sorted(payloads.items()),1)]
    inventory=dict(schema_version=1,run_id=RUN_ID,report_source=report.relative_to(R).as_posix(),input_aliases=rows,
        source_bindings=sources,runtime_bindings=runtimes,actual=dict(counts=counts,
            unittest_seconds=float(matches[0][1]),worker_seconds=worker['elapsed_worker_seconds'],
            owned_seconds=owned['elapsed_seconds'],outer_stored_seconds=final['elapsed_before_receipt_seconds'],
            cap_seconds=30,cleanup_seconds=2,cold_real_class_identity=True,owned_cleanup=True,
            scope_vi='Pure phase/claim consistency; no actualproducer/epoch/fileadmission/refit/calibration/grant'))
    recheck(inventory)
    return inventory,payloads


def recheck(inventory):
    for row in inventory['input_aliases']:
        need(sha(safe(R/row['source']).read_bytes())==row['sha256_before_copy'],'archive input drift')
    for name,digest in inventory['source_bindings'].items():
        need(sha(safe(R/name).read_bytes())==digest,'source/protocol reference drift')
    # Fingerprints only from externally pinned packet; no runtime bytes copied/imported.
    for name,digest in inventory['runtime_bindings'].items():
        need(sha(Path(name).read_bytes())==digest,'runtime fingerprint drift')


def main():
    need(os.path.normcase(os.path.abspath(sys.executable))==os.path.normcase(str(R/'.venv/Scripts/python.exe'))
         and Path(sys.prefix).resolve()==R/'.venv','repository .venv only')
    parser=argparse.ArgumentParser(description='ROOT metadata-only dry/close, không chạy test/model')
    parser.add_argument('--report',type=Path,default=CANDIDATE)
    parser.add_argument('--inventory',type=Path,required=True)
    parser.add_argument('--close',action='store_true')
    parser.add_argument('--expected-inventory-sha256')
    args=parser.parse_args();report=safe(args.report.absolute());target=safe(args.inventory.absolute(),existing=args.close)
    need(target.parent==P and target.suffix=='.json','prep-only inventory')
    need(not (R/'research_tracking/runs'/RUN_ID).exists(),'immutable bundle exists')
    inventory,payloads=gather(report);raw=encoded(inventory)
    if not args.close:
        need(not target.exists() and args.expected_inventory_sha256 is None,'exclusive dry inventory')
        with target.open('xb') as handle:handle.write(raw);handle.flush();os.fsync(handle.fileno())
        print(json.dumps(dict(status='DRY_ONLY_NOT_CLOSED',inventory_sha256=sha(raw),copies=len(payloads),actual=inventory['actual'])))
        return
    need(args.expected_inventory_sha256==sha(target.read_bytes())==sha(raw),'external reviewed exact dry SHA')
    sys.path.insert(0,str(R/'src'))
    from knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle
    note='''# GRAPH18 main selected-only contract — engineering09/11/2026

14stdlib unittest methods PASS0FES; no scientific imports/model/corpus. Real
cached stage/admission classes, no namespace stubs/reload. Per-epoch rawselection
validation duringfit80 separated from finalbestexport; old2source snapshots are
static-before-first-execution, not fakeRED. Allheads NO_EXECUTION_AUTHORITY,
no file verification; refit unavailable withoutactualexternalfreezefileverifier.
Whole30/cleanup2, actualJob0/handlesclosed/envrestored. No RSS/hardquota proof.
Sources/protocol refs/runtime fingerprints pinned, not duplicate dependencies.
Exactbytes copy+before/afterSHA; no test/model rerun when archiving. Not actual
mainproducer/epoch/admission/mainmatrix/refit/calibration/GPU/RQ completion.
'''
    previous={k:v for k,v in os.environ.items() if k.startswith('GIT_')}
    try:
        for key in list(previous):os.environ.pop(key,None)
        os.environ.update(GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='safe.directory',GIT_CONFIG_VALUE_0=R.as_posix())
        with record_evidence_run(R,RUN_ID,metadata=dict(kind='GRAPH18_PURE_MAIN_STAGE_CONTRACT_ONLY',actual=inventory['actual']),
                sources=sorted(set(payloads)|{R/name for name in inventory['source_bindings']}|{target}),note=note) as directory:
            with (directory/'inventory-before.json').open('xb') as handle:handle.write(raw)
            copied={}
            for row in inventory['input_aliases']:
                destination=directory/row['archived_as']
                with destination.open('xb') as handle:
                    handle.write(payloads[R/row['source']]);handle.flush();os.fsync(handle.fileno())
                copied[row['archived_as']]=sha(destination.read_bytes())
                need(copied[row['archived_as']]==row['sha256_before_copy'],'copy readback mismatch')
            recheck(inventory)
            with (directory/'copy-verification.json').open('xb') as handle:
                handle.write(encoded(dict(status='VERIFIED_BYTE_COPIES_NOT_RERUN',inventory_sha256=sha(raw),copied_sha256=copied,
                    sources_after={row['source']:sha(safe(R/row['source']).read_bytes()) for row in inventory['input_aliases']})))
            names=[*copied,'README.md','execution.log','inventory-before.json','copy-verification.json','force-add-files.txt','manifest.json']
            force=[(directory/name).relative_to(R).as_posix() for name in names]+list(PINS)[:2]
            if report==CANONICAL:force.append(report.relative_to(R).as_posix())
            with (directory/'force-add-files.txt').open('x',encoding='utf-8',newline='\n') as handle:handle.write('\n'.join(force)+'\n')
    finally:
        for key in list(os.environ):
            if key.startswith('GIT_'):os.environ.pop(key,None)
        os.environ.update(previous)
    verified=verify_evidence_bundle(directory);recheck(inventory)
    print(json.dumps(dict(verified=verified,manifest_sha256=sha((directory/'manifest.json').read_bytes()),
        force_add_list=(directory/'force-add-files.txt').relative_to(R).as_posix())))


if __name__=='__main__':main()
