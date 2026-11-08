"""Đóng supplement: SHA trước/sau copy; không chạy notebook/tests lần nữa."""
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[4]
PREP=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
from knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

if __name__=='__main__':
    proof=json.loads((PREP/'final-verification.json').read_bytes())
    for name,row in proof['after'].items():assert sha(ROOT/name)==row['sha256']
    selected=[ROOT/'scripts/research/build_thesis_evidence_notebook.py',ROOT/'notebooks/thesis_evidence_report.ipynb',
              ROOT/'research_tracking/reports/thesis_evidence_notebook_integrity_20261108.md']
    selected.extend(PREP/name for name in ['run_integrity.py','test_integrity.py','test_validation.py',
                    'verify_final.py','pack_integrity.py','budget.json','replacement-before.json',
                    'notebook-before.ipynb','final-verification.json'])
    for folder in ['before','after','trial01-red/source-before','trial02-green/source-before','trial03-regenerate/source-before']:
        selected.extend(sorted((PREP/folder).iterdir()))
    for trial in ['trial01-red','trial02-green','trial03-regenerate']:
        selected.extend(PREP/trial/name for name in ['execution.log','run.json'])
    assert all(path.is_file() and not path.is_symlink() for path in selected)
    inventory=[dict(source=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256_before_copy=sha(p)) for p in selected]
    os.environ.update(GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='safe.directory',GIT_CONFIG_VALUE_0=str(ROOT))
    with record_evidence_run(ROOT,'thesis-evidence-notebook-20261108-02',
        metadata=dict(kind='stored-report-single-payload-integrity-supplement-not-research',
                      previous_manifest_sha256='2100a70da6b8da2547bfeba958187b478a53f5e195e8987b1cdb1f5109eee410',
                      red_tests=3,red_failures=3,green_tests=12,green_failures=0,
                      executed_report_cells=7,verified_inputs=28,verified_claims=14,verified_pointers=104,
                      cumulative_controller_seconds=proof['cumulative_controller_seconds'],budget_seconds=30,
                      cached_outputs_unchanged=True,kernels=0,model_or_simulator_runs=0,remote_calls=0),
        sources=list(dict.fromkeys(selected)),
        note='# Notebook báo cáo — bổ sung single-payload integrity\n\nGiữ v1 bất biến; working notebook được regenerate theo đúng SHA v1 và xác minh đủ7outputs trước ghi.3race canaries nguồn cũFAIL→12checks nguồn mớiPASS; outputs7cells giống hệt v1,28inputs/14claims/104pointers. Không khoa học mới/model/simulator/kernel/remote/install. Chưa Jupyter/visual QA. Copy inventory giữ mọi alias cùng SHA trước/sau; manifest completed là integrity closure, không xóa failures lịch sử.\n') as target:
        copied={}
        for index,(source,row) in enumerate(zip(selected,inventory),1):
            digest=row['sha256_before_copy']
            if digest not in copied:
                destination=target/f'input-{index:02d}__{source.name}'
                with destination.open('xb') as handle:handle.write(source.read_bytes())
                copied[digest]=destination
            destination=copied[digest]
            row.update(destination=destination.name,sha256_after_copy=sha(destination),source_sha256_after_copy=sha(source))
            assert row['sha256_before_copy']==row['sha256_after_copy']==row['source_sha256_after_copy']
        with (target/'copy-inventory.json').open('x',encoding='utf-8') as handle:
            json.dump(dict(input_aliases=len(inventory),unique_copies=len(copied),copies=inventory),handle,ensure_ascii=False,indent=2)
            handle.write('\n')
    verification=verify_evidence_bundle(target)
    result=dict(**verification,manifest_sha256=sha(target/'manifest.json'),input_aliases=len(inventory),
                unique_copies=len(copied),physical_files=len(list(target.iterdir())),
                builder_sha256=sha(selected[0]),notebook_sha256=sha(selected[1]),report_sha256=sha(selected[2]))
    with (PREP/'closure.json').open('x',encoding='utf-8') as handle:
        json.dump(result,handle,ensure_ascii=False,indent=2);handle.write('\n')
    print(json.dumps(result))
