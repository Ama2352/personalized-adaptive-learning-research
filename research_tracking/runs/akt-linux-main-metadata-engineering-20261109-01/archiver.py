"""ROOT dry/closure cho kiểm metadata Windows; không chạy lại tests hoặc Linux."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[4]
PREP=Path(__file__).resolve().parent
RUN='akt-linux-main-metadata-engineering-20261109-01'
REPORT=ROOT/'research_tracking/reports/akt_linux_main_metadata_readiness_20261109.md'
DRAFT=PREP/'LINUX_MAIN_METADATA_REPORT_DRAFT01.md'
DRY=PREP/'linux_main_metadata_archive_dry01.json'
PINS={
    'src/knowledge_tracing/akt/research_main_execution.py':'73bbacc8c8bd196cc9d3eeb7e3ac65f27a51f3a52fa8d3fe83d14dd87ac8c7aa',
    'tests/akt/test_research_main_execution.py':'f7ed9b4dc7d28c54e3899089c5db8876d2f0fd4bf9532a901fa5eaef46431e55',
    'scripts/akt/refresh_gate2.py':'ed87ee74589087b66b434137f67388b64efb4160c41c33ff423ffc41bcc9e157',
    'tests/akt/test_gate2_refresh.py':'9c3456146634187bd9758b89b38d48c38b1364fe8d0b31a0910384f442c0cb21',
}
PREP_PINS={
    'run_linux_main_metadata_tests01.py':'7bb34d7e09c193328f81f5d7190e116b6fb08bbd090cb78713b36f23eb478968',
    'run_linux_main_metadata_tests02.py':'a73330f3c68401b4a3ab15898ed60026be53db0034649d5ce1908f0f9748ce16',
    'LINUX_CPU_MAIN_PROVENANCE_IMPLEMENTATION_PLAN01.md':'b0f960940e17a90f51ec2b384d82c8bd9100013961a126433ff821c551663d38',
    'LINUX_CPU_MAIN_PROVENANCE_IMPLEMENTATION_PLAN02.md':'d256e5d6da91f0167879136af129ed80adf9e89c339ffdfc4584bc91479a4fcd',
    'pre-linux-main-provenance01/inventory.json':'c33c8a49f4c485d5a1f1ab80c3378b4bafebc15e119d4ea5a2b99043393eed05',
    'pre-linux-gate-observation-fix01/inventory.json':'8906021163ad866c210030c74c80f30ed37fe66b7e95d5cad3877500ab951a05',
    'linux-main-provenance-source01/handoff.json':'0c07f070cf1cc1fa2ada71b2d6246638b0fa48284146c329f27ddb4435a1d2eb',
    'linux-main-metadata-tests01/result.json':'c7bbb87e39d2ef346a1ccba5bb24f99abed96e871871ad0093df7407c1a26a09',
    'linux-main-metadata-tests02/result.json':'dfcb39b7952cec091ba3f80592b4137b2fbce897ed3511f403b4b488702c14a5',
}
REFERENCES={
    'src/knowledge_tracing/akt/authorization.py':'bd6be914e3b5049927ba6358ee4872097a46469fede9ad1b71ee63df951ac7f0',
    'src/knowledge_tracing/akt/provenance.py':'493d82af749baefcacec9ece0a7abe3297e64398eb4cd93c1d639ca41752cb59',
    'src/knowledge_tracing/akt/config.py':'beb2f8830c9d411fa1c00f0acf81ffe0c5200d6c09045d949b9cebade30dc85f',
    'src/knowledge_tracing/evidence.py':'414e3d834c46d081c7d9c05beff17a3e2d9c479a0e121394aabe321929235e49',
}
GENERATED=('README.md','execution.log','copy_inventory.json','reference_inputs.json','reviewed_dry.json','closure_review.json')


def need(ok,message):
    if not ok:raise ValueError(message)


def physical(path):
    need(path.is_absolute() and path.is_relative_to(ROOT) and path.resolve()==path,'physical ROOT-bound path')
    cursor=ROOT
    need(ROOT.is_dir() and ROOT.resolve()==ROOT and not ROOT.is_symlink()
         and not getattr(ROOT,'is_junction',lambda:False)(),'physical project root')
    for part in path.relative_to(ROOT).parts:
        cursor/=part
        need(not cursor.is_symlink() and not getattr(cursor,'is_junction',lambda:False)(),'no symlink/junction')


def payload(path):
    physical(path)
    need(path.is_file() and path.stat().st_size<=4*1024**2,'bounded regular text input')
    raw=path.read_bytes()
    need(len(raw)==path.stat().st_size,'stable read size')
    return raw


def sha(path):return hashlib.sha256(payload(path)).hexdigest()


def read(path):return json.loads(payload(path))


def write(path,value):
    physical(path)
    with path.open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')


def gather(report_sha):
    need(re.fullmatch('[a-f0-9]{64}',report_sha) and sha(DRAFT)==report_sha,'ROOT-reviewed draft report SHA')
    for name,pin in PINS.items():need(sha(ROOT/name)==pin,'current four source pins')
    for name,pin in PREP_PINS.items():need(sha(PREP/name)==pin,'actual preparation/receipt pins')
    references={name:dict(sha256=pin,bytes=(ROOT/name).stat().st_size,copied=False) for name,pin in REFERENCES.items()}
    for name,item in references.items():need(sha(ROOT/name)==item['sha256'],'unchanged source dependency reference')
    copies={}

    def add(alias,path):
        need(alias not in copies and Path(alias).name==alias,'unique flat evidence alias')
        payload(path);copies[alias]=path

    for name in PINS:add('current__'+Path(name).name,ROOT/name)
    for name in ('run_linux_main_metadata_tests01.py','run_linux_main_metadata_tests02.py',
                 'LINUX_CPU_MAIN_PROVENANCE_IMPLEMENTATION_PLAN01.md',
                 'LINUX_CPU_MAIN_PROVENANCE_IMPLEMENTATION_PLAN02.md'):
        add(name,PREP/name)
    add('archiver.py',Path(__file__).resolve());add('report_snapshot.md',DRAFT)
    before=read(PREP/'pre-linux-main-provenance01/inventory.json')
    add('original__inventory.json',PREP/'pre-linux-main-provenance01/inventory.json')
    need(len(before['files'])==4,'four original snapshots')
    for row in before['files']:
        path=ROOT/row['copy'].replace('\\','/')
        need(sha(path)==row['sha256_before']==row['sha256_after'] and path.stat().st_size==row['bytes'],
             'original source before/copy preservation')
        add('original__'+path.name,path)
    first=read(PREP/'linux-main-provenance-source01/handoff.json')
    add('first_source_handoff.json',PREP/'linux-main-provenance-source01/handoff.json')
    need(len(first['source_files'])==4,'four first-version snapshots')
    for row in first['source_files']:
        path=ROOT/row['snapshot']
        need(sha(path)==row['sha256_before_copy']==row['sha256_after_copy'] and path.stat().st_size==row['bytes'],
             'first-source snapshot identity')
        references[path.relative_to(ROOT).as_posix()]=dict(sha256=sha(path),bytes=path.stat().st_size,copied=False)
    old_fixture=PREP/'linux-main-provenance-source01/test_gate2_refresh.py'
    need(sha(old_fixture)=='8f15c3d48edbca88bad8b5534c900841831e98b97d005000b46c598c7f5c9aea','actual failed fixture bytes')
    add('failed01__test_gate2_refresh.py',old_fixture)
    observation=read(PREP/'pre-linux-gate-observation-fix01/inventory.json')
    add('fixture_fix__inventory.json',PREP/'pre-linux-gate-observation-fix01/inventory.json')
    need(len(observation['files'])==4,'four pre-fixture-fix snapshots')
    for row in observation['files']:
        path=ROOT/row['copy']
        need(sha(path)==row['sha256_before_copy']==row['sha256_after_copy'] and path.stat().st_size==row['bytes'],
             'pre-fixture-fix snapshot identity')
        references[path.relative_to(ROOT).as_posix()]=dict(sha256=sha(path),bytes=path.stat().st_size,copied=False)
    identities=[];results=[]
    for attempt,failures,status,rc in (('01',14,'REJECTED',1),('02',0,'ACCEPTED_154_METADATA_REGRESSIONS',0)):
        directory=PREP/('linux-main-metadata-tests'+attempt)
        result=read(directory/'result.json');results.append(result)
        expected=dict(PINS)
        if attempt=='01':expected['tests/akt/test_gate2_refresh.py']=sha(old_fixture)
        need(result['status']==status and result['returncode']==rc and result['timeout'] is False
             and result['cap_seconds']==30 and 0<=result['elapsed_seconds']<30
             and result['source_before']==result['source_after']==expected
             and result['counts']==dict(tests=154,failures=failures,errors=0,skipped=0)
             and result['unique_case_ids']==154,'actual accepted/rejected test receipt')
        tree=ET.fromstring(payload(directory/'junit.xml'));cases=list(tree.iter('testcase'))
        ids=[(case.get('classname'),case.get('name')) for case in cases]
        need(len(ids)==len(set(ids))==154 and all(all(pair) for pair in ids),'154 unique JUnit identities')
        need(Counter(case.get('classname') for case in cases)=={
            'tests.akt.test_research_main_execution':51,'tests.akt.test_gate2_refresh':103},'actual 51/103 population')
        need(sum(len(list(case.iter('failure'))) for case in cases)==failures
             and not any(list(case.iter(tag)) for case in cases for tag in ('error','skipped')),'actual JUnit outcomes')
        identities.append(set(ids))
        if attempt=='01':
            failed=Counter(case.get('name').split('[')[0] for case in cases if list(case.iter('failure')))
            need(failed=={'test_gate2_invalid_selected_lock_rejects_before_child':6,
                'test_gate2_missing_required_pure_module_fails_before_child':7,
                'test_gate2_empty_remaining_group_is_not_silently_omitted':1},'preserved14 observation assertions')
            need('assert not observed' in payload(directory/'stdout.log').decode('utf-8')
                 and 'build_hashes' in payload(directory/'stdout.log').decode('utf-8'),'actual fixture failure diagnosis')
        for name in ('result.json','stdout.log','stderr.log','junit.xml'):add('attempt'+attempt+'__'+name,directory/name)
    need(identities[0]==identities[1],'same154 test population across attempts')
    inventory=[dict(copy=alias,source=path.relative_to(ROOT).as_posix(),sha256=sha(path),bytes=path.stat().st_size)
               for alias,path in sorted(copies.items())]
    need(len(inventory)==26 and sum(row['bytes'] for row in inventory)<1024**2,'compact exact26 selected copies')
    return inventory,references,results


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--report-sha256',required=True)
    action=parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--prepare-dry',action='store_true')
    action.add_argument('--check-dry',action='store_true')
    action.add_argument('--close',action='store_true')
    parser.add_argument('--expected-dry-sha256');parser.add_argument('--review-reference')
    args=parser.parse_args()
    need(Path(sys.prefix).resolve()==ROOT/'.venv','repository .venv only')
    destination=ROOT/'research_tracking/runs'/RUN
    physical(destination);physical(REPORT)
    need(not destination.exists() and not REPORT.exists(),'exclusive new bundle and canonical report')
    inventory,references,results=gather(args.report_sha256)
    dry=dict(run_id=RUN,canonical_report=REPORT.relative_to(ROOT).as_posix(),report_sha256=args.report_sha256,
        copies=inventory,reference_inputs=references,generated_outputs=list(GENERATED),expected_output_count=32,
        scope='WINDOWS_HOST_METADATA_TESTS_ONLY_NOT_ACTUAL_LINUX_OR_CUDA')
    if args.prepare_dry:
        write(DRY,dry)
        print(json.dumps(dict(status='DRY_PREPARED_NOT_CLOSED',dry_sha256=sha(DRY),copies=26,outputs=32)))
        return
    need(read(DRY)==dry,'reviewed dry/current exact inventory match')
    if args.check_dry:
        print(json.dumps(dict(status='DRY_MATCH_NOT_CLOSED',copies=26,outputs=32)))
        return
    need(args.expected_dry_sha256==sha(DRY) and args.review_reference,'ROOT exact-dry closure approval')
    sys.path.insert(0,str(ROOT/'src'))
    from knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle
    with REPORT.open('xb') as stream:stream.write(payload(DRAFT))
    need(sha(REPORT)==args.report_sha256,'canonical report exact reviewed draft bytes')
    note=('# Linux CPU provenance — metadata engineering trên Windows\n\n'
        'Giữ hai lượt cùng154cases:01REJECTED140PASS14FAIL vì fixture observation pollution, '
        '02ACCEPTED154PASS. Raw và source trước/sau không sửa. Additive Gate execution profile, '
        'Linux Git/source metadata và fail-closed report bindings được kiểm bằng manufactured fixtures. '
        'Chưa actual Linux source/runtime/Gate hoặc CUDA, không fit/admission/chi phí authority. '
        'Gate05 lịch sử không attests current source bytes. Wrappers timeout30s, không có Job/RSS receipt. '
        'Không copy pytest-temp/corpus/deps. Manifest chỉ chứng nhận evidence closure. '
        'Báo cáo tại ../../reports/akt_linux_main_metadata_readiness_20261109.md.\n')
    sources=list(dict.fromkeys([ROOT/row['source'] for row in inventory]+[ROOT/name for name in references]+[DRY,REPORT]))
    with record_evidence_run(ROOT,RUN,metadata=dict(kind='LINUX_MAIN_METADATA_ENGINEERING_ON_WINDOWS',
        final_tests=154,prior_tests=154,prior_pass=140,prior_fail=14,actual_linux=False,actual_cuda=False,
        training_authority=False),sources=sources,note=note) as out:
        copied=[]
        for row in inventory:
            source=ROOT/row['source'];need(sha(source)==row['sha256'],'source SHA before copy')
            with (out/row['copy']).open('xb') as stream:stream.write(payload(source))
            need(sha(source)==sha(out/row['copy'])==row['sha256'],'source/copy/source-after SHA equality')
            copied.append(dict(**row,source_sha256_after_copy=sha(source),copy_sha256=sha(out/row['copy'])))
        write(out/'copy_inventory.json',copied);write(out/'reference_inputs.json',references)
        with (out/'reviewed_dry.json').open('xb') as stream:stream.write(payload(DRY))
        need(sha(out/'reviewed_dry.json')==args.expected_dry_sha256,'reviewed dry exact copy')
        write(out/'closure_review.json',dict(reference=args.review_reference,dry_sha256=args.expected_dry_sha256,
            report_sha256=args.report_sha256,tests_rerun_at_closure=False,
            attempt01_seconds=results[0]['elapsed_seconds'],attempt02_seconds=results[1]['elapsed_seconds']))
        need({path.name for path in out.iterdir() if path.name!='manifest.json'}
             ==set(GENERATED)|{row['copy'] for row in inventory},'exact32 output population')
        need(all(sha(ROOT/row['source'])==row['sha256'] for row in inventory)
             and all(sha(ROOT/name)==item['sha256'] for name,item in references.items()),'all selected source bytes stable')
    verified=verify_evidence_bundle(destination)
    need(verified['artifacts']==32,'manifest verified32 outputs')
    print(json.dumps(dict(status='CLOSED',verification=verified,manifest_sha256=sha(destination/'manifest.json'),
        report_sha256=sha(REPORT),outputs=32,files_including_manifest=33),ensure_ascii=False))


if __name__=='__main__':main()
