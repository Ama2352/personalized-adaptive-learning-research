"""Template ROOT dry/close GRAPH11; không execute tests/model, chưa closure.

prepare-dry chỉ sau native03 terminalaccepted+externalfinalSHA+reportreview.
Binary chỉ streamhash/reference, không copy. Dryapproval là bước riêng.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]
P = Path(__file__).resolve().parent
RUN = 'cgakt-research-checkpoint-engineering-20261109-01'
DRY = P/'graph_checkpoint_archive_dry01.json'
REPORT = P/'cgakt_research_checkpoint_readiness_20261109.candidate.md'
GENERATED = ('README.md','execution.log','copy_inventory.json','binary_references.json',
    'scope.json','source_lineage.json','timing_scope.json','closure_review.json','raw_log_paths.txt')


def need(ok, message):
    if not ok: raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')


def safe(path):
    need(path.is_absolute() and path.is_relative_to(ROOT) and '..' not in path.parts, 'fixed project input')
    cursor = ROOT
    for part in ('',*path.relative_to(ROOT).parts):
        if part: cursor /= part
        need(not cursor.is_symlink() and not getattr(cursor,'is_junction',lambda:False)(), 'input alias rejected')
    need(path.resolve() == path and path.is_file(), 'regular physical input required')
    return path


def reference_hash(path, expected_bytes):
    safe(path); before = path.stat()
    need(0 <= before.st_size == expected_bytes <= 64*1024**2,'reference byte cap/exact size')
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        while chunk := stream.read(1024**2): digest.update(chunk)
    after = path.stat()
    need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)
        == (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns),'reference changed while hashing')
    return digest.hexdigest()


def gather(native_final_sha, report_sha):
    copies = {}; existence = {}
    def add(alias,path):
        safe(path);need(alias not in copies and path.stat().st_size <= 2*1024**2, 'unique bounded small copy')
        copies[alias] = path
    def load(path): return json.loads(safe(path).read_bytes())
    def raw_group(name):
        folder = P/name; need(folder.is_dir(), 'terminal raw folder required:'+name)
        for path in sorted(folder.iterdir()):
            if path.is_file(): add(name+'__'+path.name,path)
        existence[name] = sorted(p.name for p in folder.iterdir() if p.is_file())
    final_path = P/'graph-checkpoint-native03-owned/final.json'
    need(sha(safe(final_path)) == native_final_sha, 'external terminal native03 SHA')
    final = load(final_path); child = load(P/'graph-checkpoint-native03/result.json')
    packet = load(P/'graph_checkpoint_native03_allocation.json')
    need(final['status'] == 'ACCEPTED_GRAPH11_NATIVE16_STATE_PERSISTENCE_NOT_RESEARCH_FIT'
        and final['counts'] == child['counts'] == dict(tests=16,failures=0,errors=0,skipped=0), 'no closure from intent or partialnative')
    need(child['native_started'] == child['native_body_returned'] == packet['counter_caps'], 'exact native workload evidence')
    need(child['source_before'] == child['source_after'] == final['source_after'] == packet['source_pins'], 'historical source stability')
    owned = load(P/'graph-checkpoint-native03-owned/receipt.json')
    need(owned['accepted'] is True and owned['cleanup_accepted'] is True and owned['returncode'] == 0
        and owned['job_active_after_cleanup'] == 0 and owned['popen_handle_closed'] is True
        and owned['actual_worker_in_job_before_GO'] is True and owned['cleanup_errors'] == [], 'actual owned cleanup')
    tree = ET.parse(P/'graph-checkpoint-native03/junit.xml').getroot()
    need(len(list(tree.iter('testcase'))) == 16 and
        {k:sum(int(s.get(k,'0')) for s in tree.iter('testsuite')) for k in ('tests','failures','errors','skipped')}
        == final['counts'], 'raw native03 JUnit population')
    need(final['elapsed_seconds'] < 90 and child['elapsed_seconds'] < 75 and child['native_work_seconds'] < 60,
        'actual accepted elapsed budgets')
    need(child['native_proof']['direct_three_rng_restored_after_deliberate_perturbation'] is True
        and child['native_proof']['all_module_modes_restored_after_deliberate_inversion'] is True, 'direct RNG/mode evidence')
    need(sha(safe(REPORT)) == report_sha, 'reviewed report candidate bytes')
    add('source__research_graph_checkpoint.py',ROOT/'src/knowledge_tracing/akt/research_graph_checkpoint.py')
    add('source__test_research_graph_checkpoint.py',ROOT/'tests/akt/test_research_graph_checkpoint.py')
    for alias,path in list(copies.items()):
        name = path.relative_to(ROOT).as_posix(); need(sha(path) == packet['source_pins'][name], 'current component source must match actualnative')
    add('report__cgakt_research_checkpoint_readiness.md',REPORT)
    add('archive_graph_checkpoint01.py',Path(__file__).resolve())
    for name in ('CGAKT_RESEARCH_CHECKPOINT_DESIGN01.md','GRAPH11_INDEPENDENT_REVIEW01.md',
                 'GRAPH11_REVIEW_RESPONSE02.md', 'graph_checkpoint_native01_monitor_failure_note.json',
                 'graph_checkpoint_native02_inner_budget_failure_note.json'):
        add('review__'+name,P/name)
    add('writer__evidence.py',ROOT/'src/knowledge_tracing/evidence.py')
    for folder in ('graph11-test-liveness-before01','graph11-review-before02','graph11-inner-budget-before03'):
        for path in sorted((P/folder).iterdir()):
            need(path.is_file(), 'flat historical snapshot directory only');add(folder+'__'+path.name,path)
    for stage in ('pure01','pure02','pure03','native01','native02','native03'):
        for prefix in ('check','run'):
            path = P/(prefix+'_graph_checkpoint_'+stage+'.py');add(path.name,path)
        path = P/('graph_checkpoint_'+stage+'_allocation.json');add(path.name,path)
    for stage in ('02','03'):
        path = P/('check_graph_checkpoint_monitor'+stage+'.py');add(path.name,path)
        raw_group('graph-checkpoint-monitor'+stage)
    for name in ('graph-checkpoint-pure02','graph-checkpoint-pure03','graph-checkpoint-native01',
                 'graph-checkpoint-native02','graph-checkpoint-native03'):
        raw_group(name);raw_group(name+'-owned')
    for stage in ('02','03'):
        pure = load(P/('graph-checkpoint-pure'+stage+'-owned/final.json'))
        need(pure['status'] == 'ACCEPTED_GRAPH11_35_PURE_CASES_NOT_NATIVE_RESEARCH', 'actual pure35 '+stage)
        tree = ET.parse(P/('graph-checkpoint-pure'+stage+'/junit.xml')).getroot()
        need(len(list(tree.iter('testcase'))) == 35, 'raw35 JUnit '+stage)
        canary = load(P/('graph-checkpoint-monitor'+stage+'/result.json'))
        need(canary['status'] == 'ACCEPTED_5_STDLIB_MONITOR_CANARIES_NOT_NATIVE'
            and canary['counts'] == dict(tests=5,failures=0,errors=0,skipped=0), 'actual5 stdlib canary '+stage)
    failed = load(P/'graph-checkpoint-native02/result.json')
    need(failed['counts'] == dict(tests=16,failures=0,errors=16,skipped=0)
        and failed['native_body_returned']['adam_steps'] == 3, 'preserve actual shared setupfailure02')
    # Binaries stay in existing experiment outputs. Construct only the strict
    # owned UUID roots from known raw receipts, never follow arbitrarypaths.
    first = load(P/'graph-checkpoint-native01/resource-failure.json')
    ids = re.findall(r'graph11-handmade-[0-9a-f]{10}',first['error'])
    need(ids, 'original monitorfailure owned prefix')
    runs = [ids[0]]
    for stage in ('02','03'):
        value = load(P/('graph-checkpoint-native'+stage+'/result.json'))['owned_run']
        need(re.fullmatch(r'experiments/akt/results/graph11-handmade-[0-9a-f]{10}',value), 'owned later prefix')
        runs.append(Path(value).name)
    binary_refs = []
    allowed_leaves = {'epoch-1',*('authenticated-invalid-'+name for name in
        ('missing_positive','python_rng','numpy_rng','torch_rng','mode_bool','mode_name'))}
    for ordinal,name in enumerate(runs,1):
        base = ROOT/'experiments/akt/results'/name/'checkpoints'
        for leaf in sorted(base.iterdir()):
            need(leaf.is_dir() and not leaf.is_symlink() and leaf.name in allowed_leaves, 'strict owned checkpoint leaf')
            for path in sorted(leaf.iterdir()):
                safe(path)
                if path.name in ('state.pt','state.pt.pending'):
                    need(path.stat().st_size <= 64*1024**2, 'bounded reference binary')
                    size = path.stat().st_size
                    binary_refs.append(dict(source=path.relative_to(ROOT).as_posix(),bytes=size,
                        sha256=reference_hash(path,size),copied=False,attempt=ordinal,format_validity_not_implied=True))
                elif ordinal == 3 and leaf.name == 'epoch-1':
                    add(f'checkpoint{ordinal}__{leaf.name}__{path.name}',path)
                else:
                    # Không nhân đôi hàng chục metadata gần giống nhau. Metadata
                    # negative/oldpartial còn nguyên tại experiments và có SHAref.
                    need(path.stat().st_size <= 1024**2, 'bounded referenced checkpoint metadata')
                    binary_refs.append(dict(source=path.relative_to(ROOT).as_posix(),bytes=path.stat().st_size,
                        sha256=sha(path),copied=False,attempt=ordinal,reference_kind='checkpoint_metadata',
                        format_validity_not_implied=True))
    proof = child['native_proof']; valid = proof['valid_checkpoint']
    expected_binaries = {valid['directory']+'/state.pt':(valid['checkpoint_bytes'],valid['checkpoint_sha256'])}
    expected_binaries.update({r['path']:(r['bytes'],r['sha256']) for r in proof['negative_binary_references']})
    observed = {r['source']:(r['bytes'],r['sha256']) for r in binary_refs if r['attempt']==3 and r.get('reference_kind') is None}
    need(len(expected_binaries)==7 and observed==expected_binaries,'all seven physical accepted/negative03 binaries match proof')
    need(sha(copies['checkpoint3__epoch-1__metadata.json'])==valid['metadata_sha256']
        and sha(copies['checkpoint3__epoch-1__COMPLETE.json'])==valid['complete_sha256'],'physical valid03 metadata/COMPLETE matchproof')
    inventory = [dict(copy=alias,source=path.relative_to(ROOT).as_posix(),sha256=sha(path),bytes=path.stat().st_size)
        for alias,path in sorted(copies.items())]
    need(sum(r['bytes'] for r in inventory) <= 12*1024**2,'compact copied inputs12MiB cap')
    return inventory,binary_refs,existence,child,final


def main():
    parser = argparse.ArgumentParser();parser.add_argument('--prepare-dry',action='store_true');parser.add_argument('--check-dry',action='store_true')
    parser.add_argument('--native-final-sha',required=True);parser.add_argument('--report-sha',required=True)
    parser.add_argument('--close',action='store_true');parser.add_argument('--expected-dry-sha');parser.add_argument('--review-reference')
    args = parser.parse_args(); need(Path(sys.prefix).resolve()==ROOT/'.venv','repository .venv required')
    need(not(ROOT/'research_tracking/runs'/RUN).exists(),'immutable output must be absent')
    inventory,binaries,existence,child,final = gather(args.native_final_sha,args.report_sha)
    dry = dict(run_id=RUN,copies=inventory,binary_references=binaries,raw_presence=existence,
        native_final_sha256=args.native_final_sha,report_sha256=args.report_sha,
        generated_outputs=sorted(GENERATED),expected_output_count=len(inventory)+len(GENERATED))
    if args.prepare_dry:
        write(DRY,dry);print(json.dumps(dict(dry_sha256=sha(DRY),copies=len(inventory),outputs=dry['expected_output_count'])));return
    need(json.loads(DRY.read_bytes())==dry,'dry/current selected inputs drift')
    if args.check_dry: print(json.dumps(dict(status='DRY_MATCH_NOT_CLOSED',outputs=dry['expected_output_count'])));return
    need(args.close and sha(DRY)==args.expected_dry_sha and args.review_reference,'explicit Root closure review required')
    sys.path.insert(0,str(ROOT/'src'))
    from knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle
    note = '# CG-AKT — checkpoint complete-epoch CPU\n\nBằng chứng kỹ thuật handmade, không research-fit/lifecycle hoặc GPU readiness. Giữ cả hai failure; binaries chỉ reference. Native timing không throughput.\n'
    with record_evidence_run(ROOT,RUN,metadata=dict(kind='CGAKT_COMPLETE_EPOCH_PERSISTENCE_ENGINEERING_NOT_RESEARCH_FIT',
        native_counts=final['native_counts'],counts=final['counts']),sources=[ROOT/r['source'] for r in inventory],note=note) as out:
        copied=[]
        for row in inventory:
            path=ROOT/row['source'];need(sha(path)==row['sha256'],'source before copy drift')
            (out/row['copy']).write_bytes(path.read_bytes())
            need(sha(path)==sha(out/row['copy'])==row['sha256'],'pre/post/copy SHA mismatch')
            copied.append(dict(**row,source_sha256_after_copy=sha(path),copy_sha256=sha(out/row['copy'])))
        write(out/'copy_inventory.json',copied);write(out/'binary_references.json',binaries)
        write(out/'source_lineage.json',dict(native_historical_sources=child['source_before'],raw_presence=existence,
            old_versions_not_relabelled_as_executed=True,old_pure01_unexecuted=True))
        write(out/'scope.json',dict(fitted_research_model=False,lifecycle_resume_supported=False,complete_epoch=child['native_proof']['completed_epoch'],
            continuation_scope=child['native_proof']['continuation_scope'],native_final_sha256=args.native_final_sha))
        write(out/'timing_scope.json',dict(raw=child['timings'],overlap='state_validation nested insideposthook; do not add nested totals',
            interpretation='Operational observer timings in this handmade CPU fixture only; not fullcorpus/epochtraining/GPUthroughput.'))
        write(out/'closure_review.json',dict(reference=args.review_reference,dry_sha256=args.expected_dry_sha,no_reruns=True))
        (out/'raw_log_paths.txt').write_text('\n'.join(r['source'] for r in inventory if r['source'].endswith('.log'))+'\n',encoding='utf-8')
        need({p.name for p in out.iterdir() if p.name!='manifest.json'}==set(GENERATED)|{r['copy'] for r in inventory},'exact output set')
        need(all(sha(ROOT/r['source']) == r['sha256'] for r in inventory), 'all selected inputSHA unchanged after copies')
        need(all(reference_hash(ROOT/r['source'],r['bytes']) == r['sha256'] for r in binaries), 'physical references unchanged after copies; no binary deserialization')
    directory=ROOT/'research_tracking/runs'/RUN;verified=verify_evidence_bundle(directory)
    need(verified['artifacts']==dry['expected_output_count'],'closed output count')
    print(json.dumps(dict(**verified,manifest_sha256=sha(directory/'manifest.json'))))


if __name__=='__main__':main()
