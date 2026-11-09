"""Đóng proof adapter domain đã kiểm, không nạp CSV hoặc chạy tests lần nữa."""
from pathlib import Path
import hashlib
import json
import sys

ROOT=Path(__file__).resolve().parents[4]
WORK=Path(__file__).resolve().parent
RUN='paper1-pdf-domain-engineering-20261109-01'
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
if __name__=='__main__':
    if Path(sys.prefix).resolve()!=ROOT/'.venv':raise ValueError('Repository .venv')
    test=json.loads((WORK/'paper1-pdf-domain-test01/result.json').read_text(encoding='utf-8'))
    load=json.loads((WORK/'paper1_pdf_domain_actual_load01.json').read_text(encoding='utf-8'))
    assert test['status']=='ACCEPTED_SYNTHETIC_PRIMITIVES' and test['tests']==24 and test['returncode']==0
    assert test['source_before']==test['source_after'] and load['status']=='ACCEPTED_ACTUAL_PROSPECTIVE_DOMAIN_LOAD'
    assert load['input_before']==load['input_after'] and not load['reproduction_matrix_run']
    copies={'domain.py':ROOT/'src/knowledge_tracing/paper1_pdf/domain.py',
        'test_domain.py':ROOT/'tests/paper1_pdf/test_domain.py',
        'run_paper1_domain_tests01.py':WORK/'run_paper1_domain_tests01.py',
        'check_paper1_domain_actual01.py':WORK/'check_paper1_domain_actual01.py',
        'archiver.py':Path(__file__).resolve(),'actual_domain_load.json':WORK/'paper1_pdf_domain_actual_load01.json'}
    for name in ('stdout.log','stderr.log','result.json'):copies['test__'+name]=WORK/'paper1-pdf-domain-test01'/name
    references={}
    for name,pin in test['source_before'].items():
        assert sha(ROOT/name)==pin
        references[name]=pin
    for name,pin in load['input_before'].items():
        path=ROOT/load['metadata']['input_directory']/name
        assert sha(path)==pin
        references[path.relative_to(ROOT).as_posix()]=pin
    inventory={alias:dict(source=f.relative_to(ROOT).as_posix(),sha256=sha(f),bytes=f.stat().st_size) for alias,f in copies.items()}
    with (WORK/'paper1_domain_copy_inventory_before01.json').open('x',encoding='utf-8') as stream:json.dump(inventory,stream,ensure_ascii=False,indent=2)
    sys.path.insert(0,str(ROOT/'src'))
    from knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle
    with record_evidence_run(ROOT,RUN,metadata=dict(kind='PAPER1_PDF_PROSPECTIVE_DOMAIN_ENGINEERING',tests=24,
        actual_domain_loaded=True,reproduction_matrix_completed=False),sources=list(copies.values())+[ROOT/n for n in references],
        note='# Nạp domain ứng viên cho mô phỏng PDF Paper1\n\n24fixtures đạt, nạp thật5CSV đã pin thành28concept/84items/B1=25/GA=31, giữ8chapter extras riêng. Không sửa CSV, sinh đáp án hoặc chạy matrix. Các bytes là input ứng viên cho phiên bản mới, chưa chứng nhận historical PDF input identity.\n') as out:
        for alias,f in copies.items():
            assert sha(f)==inventory[alias]['sha256']
            (out/alias).write_bytes(f.read_bytes())
            assert sha(f)==sha(out/alias)==inventory[alias]['sha256']
        for name,pin in references.items():assert sha(ROOT/name)==pin
        (out/'copy_inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        (out/'reference_inputs.json').write_text(json.dumps(references,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(verify_evidence_bundle(ROOT/'research_tracking/runs'/RUN),ensure_ascii=False))
