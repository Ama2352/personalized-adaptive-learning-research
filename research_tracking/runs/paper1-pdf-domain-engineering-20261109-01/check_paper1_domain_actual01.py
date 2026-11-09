"""Chỉ đọc năm CSV đã pin để kiểm domain mới, không sinh đáp án hoặc fit."""
from pathlib import Path
import hashlib
import json
import sys
import time

ROOT=Path(__file__).resolve().parents[4]
WORK=Path(__file__).resolve().parent
if __name__=='__main__':
    start=time.perf_counter()
    if Path(sys.prefix).resolve()!=ROOT/'.venv':
        raise ValueError('Repository .venv required')
    sys.path.insert(0,str(ROOT/'src'))
    from knowledge_tracing.paper1_pdf.domain import load_prospective_paper2_domain, INPUT_DIRECTORY, INPUT_SHA256
    source=ROOT/'src/knowledge_tracing/paper1_pdf/domain.py'
    source_before=hashlib.sha256(source.read_bytes()).hexdigest()
    if source_before!='c37e32420c90f98289b9e21c2e6ea9197324f77a2452b7faae79f8c60985fb18':
        raise ValueError('Reviewed adapter required')
    before={name:hashlib.sha256((ROOT/INPUT_DIRECTORY/name).read_bytes()).hexdigest() for name,_ in INPUT_SHA256}
    domain=load_prospective_paper2_domain()
    after={name:hashlib.sha256((ROOT/INPUT_DIRECTORY/name).read_bytes()).hexdigest() for name,_ in INPUT_SHA256}
    if before!=after or before!=dict(INPUT_SHA256):
        raise ValueError('Original CSV bytes changed')
    if not domain.canonical_candidate_pins or len(domain.excluded_chapter_entries)!=8:
        raise ValueError('Actual candidate pin/extra mapping count')
    if len(domain.nodes)!=28 or len(domain.bank.items)!=84 or len(domain.baseline_edges)!=25 or len(domain.advanced_edges)!=31:
        raise ValueError('Actual candidate shape')
    if hashlib.sha256(source.read_bytes()).hexdigest()!=source_before:
        raise ValueError('Adapter changed')
    elapsed=time.perf_counter()-start
    if elapsed>=5:
        raise TimeoutError('Read-only load cap5seconds')
    result=dict(status='ACCEPTED_ACTUAL_PROSPECTIVE_DOMAIN_LOAD',elapsed_seconds=elapsed,cap_seconds=5,
        domain_identity=domain.identity,metadata=domain.metadata(),input_before=before,input_after=after,
        source_before_sha256=source_before,source_after_sha256=source_before,
        model_teacher_optimizer_calls=0,reproduction_matrix_run=False,
        scope_vi='Nạp input ứng viên và kiểm cấu trúc, chưa tái lập input lịch sử hoặc số liệu PDF.')
    with (WORK/'paper1_pdf_domain_actual_load01.json').open('x',encoding='utf-8') as stream:
        json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print(json.dumps(dict(status=result['status'],elapsed_seconds=elapsed,identity=domain.identity,concepts=28,items=84,
        baseline_edges=25,advanced_edges=31,excluded_chapter_entries=8),ensure_ascii=False))
