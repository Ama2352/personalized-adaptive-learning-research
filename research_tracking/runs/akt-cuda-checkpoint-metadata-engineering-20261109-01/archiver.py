"""ROOT đóng bằng chứng metadata B2; không chạy lại test hoặc native06."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[4]
PREP=Path(__file__).resolve().parent
RUN='akt-cuda-checkpoint-metadata-engineering-20261109-01'
DRY=PREP/'cuda_checkpoint_metadata_archive_dry01.json'
MAIN_RUN='akt-main-cuda-metadata-engineering-20261109-01'
MAIN_SHA='61f0c70915831d96118abe0125557d057cb017fb173322c819fa5ebd778d93df'
PINS={
    'check_cuda_checkpoint_metadata02.py':'5de4afeee0d43d3c77c32d90eb978ec246956f6f991f1e943bbd2aac1a76c746',
    'run_cuda_checkpoint_metadata02.py':'0c9c77f76ff330160c6a406c0518c1132569b6d7ce654ce0136946d091d02cff',
    'cuda_checkpoint_metadata02_packet.json':'6cc3254bdfb051d944c4fb077cb2e449257129e193b49b241b8f82106abd644c',
    'check_cuda_checkpoint_metadata03.py':'ffc9eb6e5ee59d5b0e508506ce86de79393cdd5323292a841adb4e698127da49',
    'run_cuda_checkpoint_metadata03.py':'1dbd2f57443a4bc89fac99bd24898ebb54790f1ad1adf23100b982317d302da1',
    'cuda_checkpoint_metadata03_packet.json':'118ac5307e1a20af2f7c0e23d138282255c267ec5dcba32183de0f43703cac71',
    'cuda-checkpoint-before01/inventory.json':'963337305d3821ff44c0706a7475dcccd583536631be3b9fd7255d780be8ae20',
    'cuda-checkpoint-before01/research_graph_checkpoint.py':'f40b47e6ea0eb090b1edd3d4ffcb0b1feb5890aa238805aafd1d26ca4896c905',
    'cuda-checkpoint-before01/test_research_graph_checkpoint.py':'332c48af10eb983433117fe994a92fccf628866e04fb24f83390a5e6ce11045e',
    'check_graph_checkpoint_native06.py':'54723442f8a2a67c91c94d42003f5a7967f84936a3f961db9845c306d06e1f55',
    'run_graph_checkpoint_native06.py':'5867c91c24902a76ef0d63030be0a8b6eb44168a103d49359ef3b122a3b1a97f',
    'graph_checkpoint_native06_allocation.json':'afb3ad71b6e633662ee9b0b33d41fd4a1b2f0cdf23f391d4f7877a273a74789d',
    'CPU_CHECKPOINT_NATIVE06_ADVERSARIAL_REVIEW01.md':'05a8fc066dec71ac841d40ddfce5a0bf0f705bba0cc0bc594e780de593ba52f7',
}
CURRENT={
    'src/knowledge_tracing/akt/research_graph_checkpoint.py':'e17e14199bc2179794a017303344ff1b67e27cdfa9035cb2a18eb85237513992',
    'tests/akt/test_research_graph_cuda_checkpoint.py':'171990ec5c733c706d7f5c9b2b659825d33c1b28f016da4d883fad698f53f35c',
    'src/knowledge_tracing/akt/config.py':'472b1b08d5270a1f2f07b214d5bf2658443265400828f6d66d1a802c1f92083d',
    'pyproject.toml':'e534173ffd5ef7303c8bae0880857fe724fda6d026426ae263ae659320b64bef',
}
OUTER_PINS={'02':'43fd33b7ca65df15d18f84c22942a7ce7275d18923b5163335d2bda440c7f433',
            '03':'0ca581457e7b0268f295ab363c30926f4c02e01b20ea0d759ef92b012cbe96d6'}
GENERATED=('README.md','execution.log','copy_inventory.json','reference_inputs.json','reviewed_dry.json','closure_review.json')


def need(value,message):
    if not value:raise ValueError(message)


def physical(path):
    need(path.is_absolute() and path.is_relative_to(ROOT) and path.resolve()==path,'physical ROOT path')
    cursor=ROOT
    for part in ('',*path.relative_to(ROOT).parts):
        cursor/=part
        need(not cursor.is_symlink() and not getattr(cursor,'is_junction',lambda:False)(),'no source/output alias')


def payload(path):
    physical(path)
    need(path.is_file() and path.stat().st_size<=2*1024**2,'bounded regular evidence')
    raw=path.read_bytes();need(len(raw)==path.stat().st_size,'stable read size')
    return raw


def sha(path):return hashlib.sha256(payload(path)).hexdigest()
def read(path):return json.loads(payload(path))


def write(path,value):
    physical(path)
    with path.open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')


def gather(report,report_sha):
    need(sha(report)==report_sha,'ROOT reviewed report bytes')
    copies={'archiver.py':Path(__file__).resolve(),'readiness_report.md':report}
    for name,pin in PINS.items():
        need(sha(PREP/name)==pin,'frozen harness/baseline/review bytes')
        copies[name.replace('/','__')]=PREP/name
    for name,pin in CURRENT.items():
        need(sha(ROOT/name)==pin,'current B2/config/readonly input bytes')
        copies['current__'+name.replace('/','__')]=ROOT/name
    packets={a:read(PREP/f'cuda_checkpoint_metadata{a}_packet.json') for a in ('02','03')}
    need({n:sha(ROOT/n) for n in packets['03']['source_pins']}==packets['03']['source_pins'],
         'all twenty current metadata project bindings including C8 remain exact')
    need(packets['02']['expected_nodeids']==packets['03']['expected_nodeids']
         and packets['02']['limits']==packets['03']['limits'],'same38IDs/resource allocation')
    summary={}
    for a,source_count in (('02',19),('03',20)):
        packet=packets[a]
        need(len(packet['source_pins'])==source_count and len(packet['runtime_pins'])==11
             and len(packet['expected_nodeids'])==len(set(packet['expected_nodeids']))==38,'actual input/identity counts')
        child_dir=PREP/f'cuda-checkpoint-metadata-tests{a}'
        owned_dir=PREP/f'cuda-checkpoint-metadata-tests{a}-owned'
        need(sha(owned_dir/'final.json')==OUTER_PINS[a],'actual ROOT outer receipt SHA')
        child,outer,owned=read(child_dir/'result.json'),read(owned_dir/'final.json'),read(owned_dir/'receipt.json')
        child_names={'native_metadata.json','pytest.log','result.json'}
        if a=='03':child_names|={'junit.xml','pytest-file.log'}
        owned_names={'final.json','GO.json','launch.json','ready.json','receipt.json','stdout.log','stderr.log'}
        need({p.name for p in child_dir.iterdir() if p.is_file()}==child_names
             and {p.name for p in owned_dir.iterdir()}==owned_names,'exact raw flat population')
        need(child['source_before']==child['source_after']==packet['source_pins']
             and child['runtime_before']==child['runtime_after']==packet['runtime_pins']
             and child['scientific_modules_absent'] is True and child['environment_and_sys_restored'] is True,'actual source/runtime/restoration')
        need(outer['owned_receipt']==owned and owned['actual_worker_in_job_before_GO'] is True
             and owned['cleanup_accepted'] is True and owned['job_active_after_cleanup']==0
             and owned['popen_handle_closed'] is True and owned['cleanup_errors']==[],'actual owned process cleanup')
        need(set(outer['outputs'])==child_names,'all original child outputs hash-bound')
        for name in sorted(child_names):
            source=child_dir/name
            need(outer['outputs'][name]==dict(bytes=len(payload(source)),sha256=sha(source)),'original raw child SHA')
            copies[a+'__child__'+name]=source
        for name in sorted(owned_names):copies[a+'__owned__'+name]=owned_dir/name
        if a=='02':
            need(outer['status']=='REJECTED_CURRENT38_METADATA_KEEP_ALL' and child['counts'] is None
                 and child['pytest_exit_code'] is None and len(child['denied'])==1
                 and Path(child['denied'][0]['details']['path'])==ROOT/'pyproject.toml'
                 and owned['returncode']==1,'preserve precollection config-read failure/countsNULL')
        else:
            need(outer['status']=='ACCEPTED_CURRENT38_CHECKPOINT_METADATA_NOT_NATIVE' and outer['errors']==[]
                 and outer['child_result']==child and owned['accepted'] is True and owned['returncode']==0
                 and child['status']=='ACCEPTED_CURRENT38_CHECKPOINT_METADATA_CHILD' and child['pytest_exit_code']==0
                 and child['error'] is None and child['denied']==[] and child['nodeids']==packet['expected_nodeids'], 'actual current38 accepted terminal')
            cases=list(ET.fromstring(payload(child_dir/'junit.xml')).iter('testcase'))
            counts=dict(tests=len(cases),failures=sum(len(list(c.iter('failure'))) for c in cases),
                errors=sum(len(list(c.iter('error'))) for c in cases),skipped=sum(len(list(c.iter('skipped'))) for c in cases))
            need(child['counts']==counts==dict(tests=38,failures=0,errors=0,skipped=0),'physical38JUnit0FES')
            need(child['resources']==dict(samples=163,observed_peak_rss_bytes=49004544,
                 observed_minimum_available_ram_bytes=2376314880),'actual03 resource samples')
        summary[a]=dict(status=outer['status'],counts=child['counts'],child_seconds=child['elapsed_seconds'],
            outer_seconds=outer['elapsed_seconds'],resources=child['resources'])
    main_manifest=ROOT/'research_tracking/runs'/MAIN_RUN/'manifest.json'
    need(sha(main_manifest)==MAIN_SHA,'immutable separate MainC78 bundle')
    baseline=read(PREP/'cuda-checkpoint-before01/inventory.json')
    for row in baseline['files']:
        need(sha(ROOT/row['copy'])==row['sha256_before_copy']==row['sha256_after_copy'],'original before-B copy inventory')
    native=read(PREP/'graph_checkpoint_native06_allocation.json')
    need(native['actual_execution'] is False and native['expected_cases']==16,'native06 proposal only')
    references=dict(mainc_bundle=dict(path=main_manifest.relative_to(ROOT).as_posix(),sha256=MAIN_SHA,copied=False),
        packet_inputs={a:dict(source_sha256=p['source_pins'],runtime_sha256=p['runtime_pins']) for a,p in packets.items()},
        current_mainc_paths=native['mainc_applied_paths'],native06_proposal_not_runtime_evidence=True,
        prior_native04=native['prior_undispatched04'],prior_native05=native['prior_undispatched05'],
        historical_native03=native['historical_native_reference'],scientific_new_N=0,actual_cuda_proof=False)
    rows=[dict(copy=alias,source=path.relative_to(ROOT).as_posix(),bytes=len(payload(path)),sha256=sha(path))
          for alias,path in sorted(copies.items())]
    need(len(rows)==41 and sum(r['bytes'] for r in rows)<1024**2,'compact exact forty-one copies')
    return rows,references,summary


def main():
    parser=argparse.ArgumentParser()
    action=parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--prepare-dry',action='store_true');action.add_argument('--check-dry',action='store_true');action.add_argument('--close',action='store_true')
    parser.add_argument('--report',type=Path,required=True);parser.add_argument('--report-sha256',required=True)
    parser.add_argument('--expected-dry-sha256');parser.add_argument('--review-reference')
    args=parser.parse_args()
    need(Path(sys.prefix).resolve()==ROOT/'.venv','repository .venv only')
    destination=ROOT/'research_tracking/runs'/RUN;physical(destination);need(not destination.exists(),'exclusive new B2 metadata bundle')
    rows,refs,summary=gather(args.report,args.report_sha256)
    dry=dict(run_id=RUN,copies=rows,reference_inputs=refs,actual_summary=summary,
        generated_outputs=list(GENERATED),expected_output_count=47,scope='CURRENT_B2_METADATA38_ONLY_KEEP_M02_PRECOLLECTION_FAILURE')
    if args.prepare_dry:
        write(DRY,dry);print(json.dumps(dict(status='DRY_PREPARED_NOT_CLOSED',sha256=sha(DRY),copies=41,outputs=47)));return
    need(read(DRY)==dry,'exact reviewed dry/current inputs')
    if args.check_dry:print(json.dumps(dict(status='DRY_MATCH_NOT_CLOSED',copies=41,outputs=47)));return
    need(args.expected_dry_sha256==sha(DRY) and args.review_reference,'ROOT exact closure approval')
    sys.path.insert(0,str(ROOT/'src'))
    from knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle
    note=('# Checkpoint CUDA BatchB —38metadata cases hiện hành\n\n'
        'M02 bị read guard chặn pyproject trước collection, countsNULL; giữ REJECTED. '
        'ROOT thêm đúng readonly SHA trong namespace03; actual03 đạt38physical0FES,20source/11runtime ổn định, '
        'env/sys khôi phục và Job0cleanup. Không import actual Torch/NumPy/Pandas, deserialize tensor hoặc chạy mô hình/CUDA. '
        'Giữ exact B2/config snapshots, before-B inventory, raw02/03 và native06 source proposal chưa phải runtime evidence. '
        'MainC78 được tham chiếu manifest riêng. Native CPU/currentGate/CUDA/fullresume tiếp tục có scope pending riêng. '
        'Đọc readiness_report.md/copy_inventory.json/reference_inputs.json; closure chỉ lưu bằng chứng.\n')
    sources=list(dict.fromkeys([ROOT/r['source'] for r in rows]+[ROOT/refs['mainc_bundle']['path'],DRY]))
    with record_evidence_run(ROOT,RUN,metadata=dict(kind='CUDA_CHECKPOINT_METADATA_ENGINEERING',tests=38,failures=0,
            errors=0,skipped=0,prior_precollection_failure_preserved=True,actual_native_or_cuda_proof=False,scientific_new_N=0),
            sources=sources,note=note) as out:
        copied=[]
        for row in rows:
            source=ROOT/row['source'];need(sha(source)==row['sha256'],'source SHA before copy')
            with (out/row['copy']).open('xb') as stream:stream.write(payload(source))
            need(sha(source)==sha(out/row['copy'])==row['sha256'],'source/copy/source-after SHA')
            copied.append(dict(**row,source_sha256_after_copy=sha(source),copy_sha256=sha(out/row['copy'])))
        write(out/'copy_inventory.json',copied);write(out/'reference_inputs.json',refs)
        with (out/'reviewed_dry.json').open('xb') as stream:stream.write(payload(DRY))
        need(sha(out/'reviewed_dry.json')==args.expected_dry_sha256,'exact reviewed dry copy')
        write(out/'closure_review.json',dict(reference=args.review_reference,dry_sha256=args.expected_dry_sha256,
            actual_summary=summary,tests_rerun=False,canonical_report_changed=False))
        need({p.name for p in out.iterdir() if p.name!='manifest.json'}==set(GENERATED)|{r['copy'] for r in rows},'exact47outputs')
        need(gather(args.report,args.report_sha256)[0]==rows,'all inputs exact after copy')
    verified=verify_evidence_bundle(destination);need(verified['artifacts']==47,'verified47outputs')
    print(json.dumps(dict(status='CLOSED_METADATA38_ONLY_NOT_NATIVE_OR_CUDA',outputs=47,files_including_manifest=48,
        manifest_sha256=sha(destination/'manifest.json'),verification=verified),ensure_ascii=False))


if __name__=='__main__':main()
