"""Inventory mặc định; chỉ đóng bundle mới sau exact report-SHA review của root."""
import argparse,hashlib,json,sys
from pathlib import Path
W=Path(__file__).resolve().parent
ROOT=W.parents[4]
RUN='akt-t4-discovery-engineering-20261108-01'
REPORT=ROOT/'research_tracking/reports/akt_t4_discovery_readiness_20261108.md'
sys.path.insert(0,str(ROOT/'src'))
from knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle

FILES=('discovery.py','discovery02.py','test_discovery.py','test_scheme02.py','discovery_profile01.json',
       'prepare_correction02.py','run_scheme_checks02.py','run_tests01.py','run_tests02.py',
       'prepare_request01.py','prepare_request02.py','derive_request02.py','source02-copy-inventory.json',
       'request-producer02-copy-inventory.json','request-contract01.json','request-contract02.json',
       'actual-cpu-discovery01-acceptance.json','actual-cpu-discovery01-launcher.json','actual-cpu-discovery01-result.json',
       'actual-cpu-discovery01-existing-logs.json','actual-cpu-discovery02-acceptance.json',
       'actual-cpu-discovery02-launcher.json','actual-cpu-discovery02-result.json',
       'coordinate_cpu_discovery01.py','coordinate_cpu_discovery02.py','verify_actual02.py',
       'actual02-independent-verification.json','README.md','CORRECTION02.md')
ABI=('actual-abi-probe01-cell.py','actual-abi-probe02-cell.py','actual-abi-probe02-provenance.json',
     'actual-abi-probe02-result.json','capture_actual_abi_probe02.py','prepare_actual_abi_probe01.py')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def inputs():
    candidates=[('source-receipts',name,W/name) for name in FILES]
    candidates += [('abi',name,W.parent/name) for name in ABI]
    for group in ('trial01','trial02','scheme-checks02'):
        candidates += [(group,p.name,p) for p in sorted((W/group).iterdir()) if p.is_file()]
    candidates += [('report',REPORT.name,REPORT),('packager',Path(__file__).name,Path(__file__)),
                   ('evidence-helper','evidence.py',ROOT/'src/knowledge_tracing/evidence.py')]
    unique={};occurrences=[]
    for group,name,path in candidates:
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(ROOT):
            raise ValueError('unsafe/missing selected evidence: '+str(path))
        raw=path.read_bytes();raw.decode('utf-8-sig')
        digest=hashlib.sha256(raw).hexdigest()
        alias=group+'__'+name
        if digest not in unique:unique[digest]=(alias,path)
        occurrences.append({'group':group,'source_path':path.relative_to(ROOT).as_posix(),'bytes':len(raw),
                            'sha256_before_copy':digest,'archive_name':unique[digest][0]})
    return unique,{'kind':'DISCOVERY_CPU_ONLY_INPUT_INVENTORY','occurrences':occurrences,
                   'input_occurrences':len(occurrences),'unique_SHA_inputs':len(unique),
                   'exclusions':['private RPC/rawbridge state','request JSON/cells containing encoded source payload',
                                 'test temporary source/venv fixtures','ZIP/wheels/installed venv/binary/model/data artifacts'],
                   'limits':'Hash integrity only. Actual warm CPU discovery is not GPU ready, normal-startup audit or authorization.'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--inventory-output',type=Path,required=True)
    p.add_argument('--close-after-root-review',action='store_true')
    p.add_argument('--reviewed-report-sha256')
    a=p.parse_args()
    unique,inventory=inputs()
    a.inventory_output.open('x',encoding='utf-8').write(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n')
    if not a.close_after_root_review:
        print(json.dumps({'status':'DRY_INVENTORY_NO_BUNDLE_CREATED','occurrences':len(inventory['occurrences']),'unique_SHA_inputs':len(unique)}));return
    if sha(REPORT)!=a.reviewed_report_sha256:raise ValueError('exact root-reviewed report SHA required')
    with record_evidence_run(ROOT,RUN,metadata={'kind':'ACTUAL_READONLY_CPU_DISCOVERY_ENGINEERING',
            'unique_input_count':len(unique),'actual_status':'WARM_CANDIDATE_REQUIRES_AUDIT',
            'GPU_ready':False,'normal_startup_accepted':False,'model_imports_or_installs':0},
            sources=[path for _,path in unique.values()],note='# Discovery CPU trước T4\n\nActual warm candidate, không GPU ready/authorization. Giữ actual01 failed, local timeout và old2FAIL→new2PASS; xem report snapshot/copy inventory.\nPrefix /usr là actual no-site prefix, chưa là normal startup venv proof. Metadata/entrypoint fingerprints chưa là full installed-site-byte attestation. Không raw private RPC/base64 request/cell payload/wheels/venv/binary.\n') as out:
        for digest,(alias,path) in unique.items():
            raw=path.read_bytes()
            if hashlib.sha256(raw).hexdigest()!=digest:raise ValueError('source drift before copy')
            (out/alias).open('xb').write(raw)
            if sha(out/alias)!=digest or sha(path)!=digest:raise ValueError('source/copy SHA drift')
        inventory['sha256_after_copy']={alias:sha(out/alias) for alias,_ in unique.values()}
        (out/'copy-inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(verify_evidence_bundle(ROOT/'research_tracking/runs'/RUN)))


if __name__=='__main__':main()
