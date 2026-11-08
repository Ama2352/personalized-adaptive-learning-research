"""ROOT review/dry/closure; chỉ metadata/SHA/copy, không rerun native hoặc tests."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[4]
PREP=Path(__file__).resolve().parent
DRY=PREP/'sakt_checkpoint_counter_delta_dry02.json'
RUN='sakt-research-checkpoint-counter-delta-20261109-01'
HELPER=ROOT/'src/knowledge_tracing/evidence.py'
HELPER_SHA='414e3d834c46d081c7d9c05beff17a3e2d9c479a0e121394aabe321929235e49'
SOURCE='40fa69b861fb93d565fb2a37a0f126509c5239e681fdf3a3c5ae022f3b6cb3c7'
TEST='e7a144ac5fafff4d90c2f0ae5613fbbd261db76f43c906d9aa61fed207e4a2c0'
COUNTS=dict(constructors=2,forwards=5,logical_backwards=3,adam_constructors=2,adam_steps=3,
    torch_save_calls=13,torch_load_calls=23,model_state_restores=2,optimizer_state_restores=2)
GENERATED={'README.md','execution.log','approved_dry_inventory.json','copy_inventory_before.json',
    'copy_inventory_after.json','frozen_acceptance.json','binary_references.json','closure_review.json','raw_log_paths.txt'}
NOTE='''# SAKT: strict cumulative Adam counter delta

Actual native02:33PASS,3logical Adam bodies,0FES. New guard đòi mọi Adam state
step bằng cumulative progress, thay vì chỉ positive/<=. Epoch2 roundtrip cùng
authenticated stale-step1/counter2 và wrongpreviousSAVE đã có passed regressions.
Chỉ Adam đã numeric roundtrip; không SGD/mid-epoch/fullresearchresume/selectedfit.

Bundle70 lịch sử được tham chiếu exactmanifest378046, không sửa hoặc copy lại
30sourcefiles. Source/test40fa/e7a, reviewedpatch/apply receipts, fresh02controller/
allocation/raw33/JUnit/ownedcleanup và small counter2metadata được giữ riêng.
Freeze154 source-only là lịch sử tại targeted02, không trainingpermission.

Không copy .pt/cache; chỉ SHA references cho epoch2 positive và stale2 negative.
Archiver không torch.load/fit/pytest hoặc kiểm tensor lần nữa; bằng chứng tensor
dựa actualpassed source-bound tests, binary gốc vẫn cần nếu muốn inspect độc lập.
Copy inventory/manifest kiểm SHA,size,exactoutputset; không RQ efficacy proof.
'''


def need(ok,message):
    if not ok:raise ValueError(message)


def physical(path):
    path=path.absolute();need(path.is_relative_to(ROOT) and ROOT.resolve()==ROOT.absolute(),'physical workspace only')
    cursor=ROOT
    need(not cursor.is_symlink() and not getattr(cursor,'is_junction',lambda:False)(),'root alias')
    for part in path.relative_to(ROOT).parts:
        need(part not in ('.','..'),'unsafe path');cursor/=part
        need(not cursor.is_symlink() and not getattr(cursor,'is_junction',lambda:False)(),'path alias')
    need(path.resolve()==path,'physical path required');return path


def sha(path):
    path=physical(path);need(path.is_file() and path.stat().st_size<=2*1024**2,'small bounded evidence only')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    sha(path);return json.loads(path.read_text(encoding='utf-8-sig'))


def write(path,value):
    with path.open('x',encoding='utf-8') as stream:json.dump(value,stream,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);stream.write('\n')


def check():
    dry=read(DRY);need(dry['run_id']==RUN,'fixed bundle identity')
    reference=dry['prior_closed_bundle']
    need(reference['manifest_sha256']=='378046f4605a431d4a404975cb46201f8b982d059736d34d329bf26ceacb4611'
         and sha(ROOT/reference['manifest_path'])==reference['manifest_sha256'],'closed70 reference pin')
    prior=read(ROOT/reference['manifest_path'])
    need(prior['status']=='completed' and len(prior['outputs_sha256'])==70,'historical70 exact output population')
    need(sha(HELPER)==HELPER_SHA,'evidence helper pin')
    aliases=set();paths=set()
    for row in dry['copies']:
        path=physical(ROOT/row['source']);name=row['copy']
        need(path.suffix not in ('.pt','.pth','.ckpt') and path.is_file(),'no binary model copies')
        need(name not in aliases and '/' not in name and '\\' not in name and row['source'] not in paths,'unique flat copies')
        need(sha(path)==row['sha256'] and path.stat().st_size==row['bytes'],'selected source hash/size drift')
        aliases.add(name);paths.add(row['source'])
    for row in dry['binary_references']:
        path=physical(ROOT/row['source'])
        need(path.is_relative_to(ROOT/'artifacts/akt/local-tests/skrc02') and path.suffix=='.pt','new synthetic binary reference only')
        need(sha(path)==row['sha256'] and path.stat().st_size==row['bytes'],'binary reference SHA/size drift')
    need(sha(ROOT/'src/knowledge_tracing/sakt/research_checkpoint.py')==SOURCE
         and sha(ROOT/'tests/sakt/test_research_checkpoint.py')==TEST,'accepted source revision')
    allocation=read(PREP/'sakt_research_checkpoint02_allocation.json')
    child=read(PREP/'sakt-research-checkpoint02/result.json');final=read(PREP/'sakt-research-checkpoint02-owned/final.json')
    owned=read(PREP/'sakt-research-checkpoint02-owned/receipt.json')
    need(final['status']=='ACCEPTED_SAKT_RESEARCH_CHECKPOINT_FIXTURES_NOT_RESEARCH_FIT'
         and final['native_counts']==child['native_started']==child['native_body_returned']==COUNTS,'actual native counters')
    need(final['counts']==child['counts']==dict(tests=33,failures=0,errors=0,skipped=0)
         and child['pytest_exit_code']==0 and child['original_exception'] is None and child['junit_error'] is None,'actual33 cases')
    suites=ET.parse(PREP/'sakt-research-checkpoint02/junit.xml').getroot()
    actual={key:sum(int(s.get(key,'0')) for s in suites.iter('testsuite')) for key in ('tests','failures','errors','skipped')}
    need(actual==final['counts'] and len(list(suites.iter('testcase')))==33,'raw JUnit population')
    need(owned['accepted'] and owned['cleanup_accepted'] and owned['job_active_after_cleanup']==0
         and owned['popen_handle_closed'] and owned['returncode']==owned['worker_returncode_before_cleanup']==0,'owned cleanup/terminal')
    need(0<=final['elapsed_seconds']<90 and 0<=child['elapsed_seconds']<83,'accepted elapsed scopes')
    need(child['source_before']==child['source_after']==allocation['source_pins']
         and child['frozen154_before']==child['frozen154_after']==allocation['frozen_gate_reference']['gate_build_hashes'],'tested source maps')
    need(child['resources']['observed_peak_rss_bytes']<=536870912
         and child['resources']['observed_minimum_available_ram_bytes']>=1073741824
         and not child['forbidden_attempts'] and child['monitor_stopped'] and not child['monitor_errors'],'resource/scope guards')
    for folder in ('sakt-research-checkpoint02','sakt-research-checkpoint02-owned'):
        for marker in ('resource-failure.json','postwrite_rejection.json'):
            need(not (PREP/folder/marker).exists(),'late failure overrides acceptance')
    need(dry['generated_outputs']==sorted(GENERATED) and dry['expected_output_count']==len(aliases)+len(GENERATED),'output count exact')
    need(not (aliases&GENERATED),'copy/generated name overlap')
    return dry


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check-dry',action='store_true');parser.add_argument('--close',action='store_true')
    parser.add_argument('--expected-dry-sha256');parser.add_argument('--review-reference');args=parser.parse_args()
    need(args.check_dry!=args.close,'choose one explicit dry-check or ROOT-approved closure')
    dry=check()
    if args.check_dry:
        print(json.dumps(dict(status='DRY_INPUTS_VERIFIED_NOT_CLOSED',dry_sha256=sha(DRY),copies=len(dry['copies']),
                              binary_references=len(dry['binary_references']),expected_outputs=dry['expected_output_count'])));return
    need(args.expected_dry_sha256 is not None and sha(DRY)==args.expected_dry_sha256,'exact reviewed dry SHA required')
    need(type(args.review_reference) is str and bool(args.review_reference.strip()),'concrete ROOT closure review required')
    spec=importlib.util.spec_from_file_location('pinned_evidence_helper',HELPER);evidence=importlib.util.module_from_spec(spec);spec.loader.exec_module(evidence)
    sources=[ROOT/x['source'] for x in dry['copies']]+[ROOT/x['source'] for x in dry['binary_references']]+[DRY]
    facts=dict(dry['facts'],approved_dry_sha256=args.expected_dry_sha256,closure_review_reference=args.review_reference)
    with evidence.record_evidence_run(ROOT,RUN,metadata=facts,sources=sources,note=NOTE) as directory:
        with DRY.open('rb') as src,(directory/'approved_dry_inventory.json').open('xb') as dst:shutil.copyfileobj(src,dst)
        write(directory/'copy_inventory_before.json',dry['copies']);after=[]
        for row in dry['copies']:
            source=ROOT/row['source'];target=directory/row['copy']
            need(sha(source)==row['sha256'],'precopy source drift')
            with source.open('rb') as src,target.open('xb') as dst:shutil.copyfileobj(src,dst)
            need(sha(source)==sha(target)==row['sha256'] and target.stat().st_size==row['bytes'],'copy pre/post hash/size drift')
            after.append(dict(row,source_sha256_after=sha(source),copy_sha256=sha(target)))
        write(directory/'copy_inventory_after.json',after);write(directory/'frozen_acceptance.json',dry['facts'])
        write(directory/'binary_references.json',dry['binary_references'])
        write(directory/'closure_review.json',dict(reference=args.review_reference,dry_sha256=args.expected_dry_sha256,
            tests_rerun=False,model_or_optimizer_calls=0,fullGate_verdict_claimed=False))
        (directory/'raw_log_paths.txt').write_text('\n'.join(x['source'] for x in dry['copies'] if x['source'].endswith(('.log','.xml','.jsonl')))+'\n',encoding='utf-8')
        need({p.name for p in directory.iterdir()}=={x['copy'] for x in dry['copies']}|GENERATED|{'manifest.json'},'exact output membership')
    directory=ROOT/'research_tracking/runs'/RUN;verified=evidence.verify_evidence_bundle(directory)
    need(verified['artifacts']==dry['expected_output_count'],'verified output count')
    print(json.dumps(dict(bundle=directory.relative_to(ROOT).as_posix(),manifest_sha256=sha(directory/'manifest.json'),**verified)))


if __name__=='__main__':main()
