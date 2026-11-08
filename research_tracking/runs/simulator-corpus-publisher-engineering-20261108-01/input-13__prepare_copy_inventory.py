"""Dry inventory cho parent archive; không copy/đóng bundle hoặc chạy tests."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
PREP=Path(__file__).resolve().parent

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

if __name__=='__main__':
    files=[ROOT/'src/knowledge_tracing/simulator_corpus_publisher.py',
           ROOT/'tests/shared_kt/test_simulator_corpus_publisher.py',
           ROOT/'research_tracking/reports/simulator_corpus_publisher_readiness_20261108.md']
    files.extend(PREP/name for name in ['DESIGN01.md','ROUNDTRIP_ADDENDUM01.md',
        'publisher-proposal01-before-roundtrip.py','roundtrip-amendment-before.json',
        'run_pure.py','verify_final.py','final-verification.json','budget.json',
        'peer-review-messages.json','prepare_copy_inventory.py'])
    files.extend(PREP/'trial01'/name for name in ['pytest.log','pytest.xml','run.json'])
    files.extend(sorted((PREP/'trial01/source-before').iterdir()))
    copied={};rows=[]
    for index,path in enumerate(files,1):
        assert path.is_file() and not path.is_symlink()
        digest=sha(path)
        destination=copied.setdefault(digest,f'input-{index:02d}__{path.name}')
        rows.append(dict(source=path.relative_to(ROOT).as_posix(),bytes=path.stat().st_size,
                         sha256_before_copy=digest,proposed_destination=destination))
    result=dict(status='DRY_COPY_INVENTORY_NOT_ARCHIVE_CLOSED',
        proposed_run='simulator-corpus-publisher-engineering-20261108-01',
        input_aliases=len(rows),unique_content_files=len(copied),inputs=rows,
        excludes_vi='Không tmpFS corpora/oracle fixtures, protected dataset, binaries, private RPC hoặc old bundles.')
    with (PREP/'copy-inventory-before.json').open('x',encoding='utf-8') as handle:
        json.dump(result,handle,ensure_ascii=False,indent=2);handle.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='inputs'}))
