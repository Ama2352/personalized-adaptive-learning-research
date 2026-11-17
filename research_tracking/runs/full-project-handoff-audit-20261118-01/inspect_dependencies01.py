"""Lập allowlist đầu vào bàn giao và rà metadata các bản trùng đã kiểm lịch sử."""
from collections import Counter
from pathlib import Path
import csv
import hashlib
import json
import os
import subprocess

ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def write(name,value):
    (B/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def files(relative):
    path=ROOT/relative
    if path.is_file():
        return [path]
    return sorted(p for p in path.rglob('*') if p.is_file() and '__pycache__' not in p.parts)


def main():
    mandatory={
        'CANONICAL_JUNYI_AND_SPLITS':[
            'artifacts/bkt_baseline/derived/canonical',
            'artifacts/bkt_baseline/derived/manifest.json',
            'artifacts/bkt_baseline/derived/duplicate_lineage.parquet',
            'artifacts/bkt_baseline/splits'],
        'GAM_SOURCE_MAP':['artifacts/gam_kt/derived/source_map'],
        'GRADE10_MAIN_CORPUS':['artifacts/simulator/corpora/grade10-development-lifecycle01-20261108'],
        'ROLES_AND_REFIT_INDEX':['artifacts/akt/junyi-roles/outer4-research-v1-20261112-01',
                                'artifacts/akt/refit-inputs'],
        'EXERCISE_AND_GRAPH_SOURCE':['dataset/junyi_Exercise_table.csv',
            'dataset/relationship_annotation_training.csv','dataset/relationship_annotation_testing.csv'],
    }
    groups=[]
    for name,roots in mandatory.items():
        rows=[]
        for relative in roots:
            for path in files(relative):
                rows.append(dict(path=path.relative_to(ROOT).as_posix(),bytes=path.stat().st_size,sha256=sha(path)))
        groups.append(dict(name=name,files=rows,bytes=sum(r['bytes'] for r in rows),
                           drive_coverage='Chưa có gói bàn giao riêng được nghiệm thu cho toàn nhóm; có thể có bản sao trong archive lịch sử, cần chọn đường phục hồi rõ ràng.'))
        print('INPUT_GROUP_HASHED',name,len(rows),sum(r['bytes'] for r in rows),flush=True)
    raw=ROOT/'dataset/junyi_ProblemLog_original.csv'
    raw_sha=sha(raw)
    manifest=json.loads((ROOT/'artifacts/bkt_baseline/derived/manifest.json').read_text(encoding='utf-8'))
    assert raw_sha==manifest['input_sha256']
    raw_record=dict(path=raw.relative_to(ROOT).as_posix(),bytes=raw.stat().st_size,sha256=raw_sha,
        role='Nguồn gốc phục vụ tái lập preprocessing. Có canonical/splits đã nghiệm thu thì có thể chạy phần còn lại trước; giữ hoặc chuyển raw riêng để tái lập từ đầu.')
    write('REQUIRED_INPUTS01.json',dict(status='EXACT_LOCAL_INPUTS_HASHED_NO_TRANSFER',
        groups=groups,total_bytes=sum(g['bytes'] for g in groups),raw_provenance=raw_record,
        holdout_boundary='Canonical và annotations chứa nhiều role. Chỉ dùng development theo assignments/roles đã frozen; giữ Test tách khỏi chọn cấu hình.',
        oracle_boundary='Grade10 oracle sidecar chỉ dùng world/diagnosis; KT đọc observable role shards.'))
    # Rà metadata trước đây; kết quả này không cấp quyền dọn file.
    counters=Counter();sizes=Counter();examples=[]
    source=ROOT/'experiments/akt/results/artifact-offload-20261116-01/UNUSED.csv'
    with source.open(encoding='utf-8-sig',newline='') as stream:
        for row in csv.DictReader(stream):
            if row['category']!='UNUSED_VERIFIED_DUPLICATE':
                continue
            path=ROOT/row['path'];keeper=ROOT/row['keeper']
            counters['catalog_rows']+=1;sizes['catalog_bytes']+=int(row['bytes'])
            if not path.is_file() or not keeper.is_file():
                counters['missing_source_or_keeper']+=1;examples.append(row['path']);continue
            stat=path.stat()
            if stat.st_size==int(row['bytes']) and keeper.stat().st_size==stat.st_size and stat.st_mtime_ns==int(row['modified_ns']):
                counters['size_mtime_keeper_match']+=1;sizes['size_mtime_keeper_match_bytes']+=stat.st_size
            else:
                counters['metadata_changed']+=1;examples.append(row['path'])
    write('DUPLICATE_REVIEW01.json',dict(status='HISTORICAL_SHA_CATALOG_CURRENT_METADATA_REVIEW',
        counts=dict(counters),bytes=dict(sizes),exceptions=examples[:30],
        limit='SHA từng bản đã kiểm trong catalog16/11; lượt này đối chiếu tồn tại/size/mtime/keeper. Chưa hash lại55,78GB và không duyệt xóa.'))
    tracked=[p for p in subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0') if p]
    untracked=[p for p in subprocess.check_output(['git','ls-files','--others','--exclude-standard','-z'],cwd=ROOT).decode().split('\0') if p]
    write('CODE_AND_LOCAL_WORK01.json',dict(head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),
        tracked_files=len(tracked),tracked_private_paths=[p for p in tracked if '/private/' in p],
        modified_files=subprocess.check_output(['git','diff','--name-only'],cwd=ROOT).decode().splitlines(),
        untracked_files=[dict(path=p,bytes=(ROOT/p).stat().st_size) for p in untracked if (ROOT/p).is_file()],
        note='Clone/nhận source current cùng hồ sơ nghiên cứu; rà và snapshot riêng phần chưa commit. .venv/venv/.wsl là môi trường có thể dựng lại.'))
    print('DEPENDENCY_AUDIT_COMPLETE',sum(g['bytes'] for g in groups),'RAW',raw.stat().st_size,'DUPLICATES',dict(counters),flush=True)


if __name__=='__main__':
    main()
