"""GRAPH04 dry SHA inventory trước closure; không test/model hoặc sửa oldbundle."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys

ROOT=Path.cwd().resolve();PREP=Path(__file__).resolve().parent
ADAPTER=PREP.parent/'graph-training-adapter-20261108-01'
REPORT=ROOT/'research_tracking/reports/akt_graph_training_readiness_20261108.md'
RUN='akt-graph-training-engineering-20261108-01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_bytes())


def collect():
    # Chỉ các thư mục evidence đã terminal; không caches/tmp/Parquet/binaries/private.
    paths=set()
    def add(path):
        p=path.absolute()
        assert p.is_relative_to(ROOT) and p.is_file() and not p.is_symlink()
        assert p.stat().st_size<=2*1024**2 and p.suffix not in ('.pt','.zip','.parquet','.csv.gz')
        assert not any(x in p.parts for x in ('.git','.venv','dataset','credentials','cache','tmp','__pycache__'))
        paths.add(p)
    for directory in [PREP,ADAPTER]+[PREP/x for x in
            ('actual01','actual02','callback-pure01','callback-pure02','inventory-correction01')]+[
            ADAPTER/x for x in ('pure01','pure02','pre-parent-review-gate0')]:
        for p in directory.iterdir():
            if p.is_file() and not (p.name.startswith('dry_inventory') and p.suffix=='.json'):add(p)
    facts=read(PREP/'archive_facts.json')
    for name in facts['selected_output_paths']:add(ROOT/name)
    for name in facts['current_source_sha256']:add(ROOT/name)
    # Giữ full dependency SHA trong receipts; chỉ copy bodies của changed targets.
    for name,h in read(PREP/'actual02/receipt.json')['source_before'].items():
        if name=='tests/akt/test_simulator_engineering.py':
            assert sha(PREP/'test_simulator_engineering.before_inventory_correction.py')==h
        else:assert sha(ROOT/name)==h
    for name in ('src/knowledge_tracing/evidence.py',
                 'artifacts/akt/local-tests/graph-confidence-gate-20261108-01/NEXT_GRAPH_LIFECYCLE_CONTRACT.md'):
        add(ROOT/name)
    add(REPORT)
    grouped={}
    for p in sorted(paths):
        h=sha(p)
        if h not in grouped:
            label=re.sub(r'[^A-Za-z0-9_.-]','_',p.name)
            grouped[h]=dict(copy=f'input-{len(grouped):03d}-{h[:12]}-{label}',
                           bytes=p.stat().st_size,sha256_before_copy=h,sources=[])
        grouped[h]['sources'].append(p.relative_to(ROOT).as_posix())
    return sorted(grouped.values(),key=lambda r:r['copy'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=('dry-run','close'))
    parser.add_argument('--approved-report-sha256');parser.add_argument('--approved-inventory-sha256')
    parser.add_argument('--approval-reference')
    a=parser.parse_args()
    assert Path(sys.prefix).resolve()==ROOT/'.venv'
    # Reuse a stdlib verifier by definitions; its __main__ output writer is not run.
    ns={'__file__':str(PREP/'verify_archive_inputs.py'),'__name__':'archive_validation'}
    exec(compile((PREP/'verify_archive_inputs.py').read_bytes(),str(PREP/'verify_archive_inputs.py'),'exec'),ns)
    facts=ns['verify']();assert facts==read(PREP/'archive_facts.json')
    review=read(PREP/'parent-raw-lifecycle-review.json')
    assert review['status']=='PASS_PARENT_GRAPH_LIFECYCLE_RAW_ARTIFACT_REVIEW' and review['global_updates']==4
    for row in review['outputs']:
        assert sha(ROOT/row['path'])==row['sha256'] and (ROOT/row['path']).stat().st_size==row['bytes']
    rows=collect();inventory_path=PREP/'dry_inventory_v2.json'
    future=ROOT/'research_tracking/runs'/RUN
    for link in re.findall(r'\]\(([^)]+)\)',REPORT.read_text(encoding='utf-8')):
        target=(REPORT.parent/link).resolve()
        if target.parent==future:assert target.name in {r['copy'] for r in rows},link
        else:assert target.exists(),link
    binaries=facts['binary_references_not_copied']
    for row in binaries:
        p=ROOT/row['path'];assert p.suffix=='.pt' and p.stat().st_size<=8*1024**2 and sha(p)==row['sha256']
    if a.operation=='dry-run':
        inventory=dict(status='DRY_INPUT_INVENTORY_NOT_CLOSED',run_id=RUN,report_sha256=sha(REPORT),
            facts_sha256=sha(PREP/'archive_facts.json'),helper_sha256=sha(Path(__file__)),
            copy_pairs=len(rows),input_path_aliases=sum(len(r['sources']) for r in rows),inputs=rows,
            binary_references_not_copied=binaries,planned_outputs=len(rows)+7,planned_total_files=len(rows)+8,
            closure_authorized=False,model_test_optimizer_reruns=0)
        with inventory_path.open('x',encoding='utf-8') as f:json.dump(inventory,f,ensure_ascii=False,indent=2)
        print(json.dumps({k:inventory[k] for k in ('status','copy_pairs','input_path_aliases','planned_outputs','planned_total_files','report_sha256','helper_sha256')}|dict(dry_inventory_sha256=sha(inventory_path))))
        return
    assert a.approval_reference and a.approval_reference.strip()
    assert a.approved_report_sha256==sha(REPORT) and a.approved_inventory_sha256==sha(inventory_path)
    assert read(inventory_path)['inputs']==rows
    assert read(inventory_path)['binary_references_not_copied']==binaries
    # Exact safe.directory is process-only; no Git mutation/global setting.
    count=int(os.environ.get('GIT_CONFIG_COUNT','0'))
    os.environ[f'GIT_CONFIG_KEY_{count}']='safe.directory';os.environ[f'GIT_CONFIG_VALUE_{count}']=str(ROOT)
    os.environ['GIT_CONFIG_COUNT']=str(count+1)
    sys.path.insert(0,str(ROOT/'src'))
    from knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle
    metadata=dict(kind='GRAPH_AKT_TOY_LIFECYCLE_ENGINEERING_WITH_RETAINED_FAILURES',
        scope_verdict=facts['status'],actual02_raw_counts=facts['actual02_counts'],whole_gate_pass_claimed=False,
        global_optimizer_reservations=4,global_optimizer_body_returns=4,graph_complete_steps=1,graph_partial_steps=1,
        actual_and_readonly_seconds=facts['actual_plus_readonly_cumulative_seconds'],actual_cap_seconds=60,
        approved_report_sha256=sha(REPORT),approved_inventory_sha256=sha(inventory_path),
        parent_review_sha256=sha(PREP/'parent-raw-lifecycle-review.json'),closure_approval_reference=a.approval_reference,
        binary_references_not_copied=binaries,fitted_research=False,resume_supported=False,
        scientific_S04_S05_adoption=False,archive_model_or_test_reruns=0)
    note='''# GRAPH04: bằng chứng lifecycle graph-aware handmade CPU toy

34pure adapterPASS+8callbackPASS; actual01RAMfloor failure0updates giữ nguyên. Actual02 raw45PASS1FAIL, trong đó6graph tests PASS: graphcomplete1step8targets, selection4=3known+1OOV, reload0, allbranch/gate changes; graphpartial1step không checkpoint/COMPLETE. Tổng4global steps gồm basehappy/basepartial; oldbase inventoryfixture sửa và gọi lại riêng với storedartifact,0update. Không đổi thành46suitePASS. Actual+readonly46,688882/60s. Binary chỉ SHArefs tại outputgốc. Không researchfit/calibration/OnlineSession/resume/S04S05/GPU hoặc fullGate. Archive completed chỉ có nghĩa copy/SHA integrity; xem report/receipts cho giới hạn. Không sửa sau closure.
'''
    dependencies={ROOT/n for n in read(PREP/'actual02/receipt.json')['source_before']
                  if n!='tests/akt/test_simulator_engineering.py'}
    sources=sorted({ROOT/n for r in rows for n in r['sources']}|{inventory_path}|{ROOT/r['path'] for r in binaries}|dependencies)
    with record_evidence_run(ROOT,RUN,metadata=metadata,sources=sources,note=note) as directory:
        after=[]
        for row in rows:
            shutil.copyfile(ROOT/row['sources'][0],directory/row['copy'])
            h=sha(directory/row['copy'])
            assert h==row['sha256_before_copy'] and all(sha(ROOT/n)==h for n in row['sources'])
            after.append(row|dict(sha256_after_copy=h,exact_match=True))
        shutil.copyfile(inventory_path,directory/'approved_dry_inventory.json')
        assert sha(directory/'approved_dry_inventory.json')==a.approved_inventory_sha256
        def write(name,value):
            with (directory/name).open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2)
        write('copy_inventory_before.json',rows);write('copy_inventory_after.json',after)
        write('archive_verdict.json',metadata)
        names={r['copy'] for r in rows}|{'README.md','execution.log','approved_dry_inventory.json',
            'copy_inventory_before.json','copy_inventory_after.json','archive_verdict.json','force_add_paths.txt'}
        with (directory/'force_add_paths.txt').open('x',encoding='utf-8') as f:
            f.write(''.join((directory/n).relative_to(ROOT).as_posix()+'\n' for n in sorted(names|{'manifest.json'})))
    verified=verify_evidence_bundle(directory)
    assert set(read(directory/'manifest.json')['outputs_sha256'])==names
    assert {p.name for p in directory.iterdir()}==names|{'manifest.json'}
    print(json.dumps(verified|dict(manifest_sha256=sha(directory/'manifest.json'),total_files=len(names)+1,
        force_add_paths=str(directory/'force_add_paths.txt'))))


if __name__=='__main__':main()
