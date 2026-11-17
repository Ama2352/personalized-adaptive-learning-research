"""Pin đầu vào chuẩn và model trước/sau đợt dọn, không nạp tensor."""
from pathlib import Path
import json,hashlib,sys,concurrent.futures
ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent

def pin(row):
    path=ROOT/row['path']
    with path.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
    assert digest==row['sha256'] and path.stat().st_size==row['bytes'],row['path']
    return dict(path=row['path'],bytes=row['bytes'],sha256=digest)

def main():
    after='--after' in sys.argv
    if after:rows=json.loads((B/'PROTECTED_BEFORE.json').read_text(encoding='utf-8'))['files']
    else:
        required=json.loads((ROOT/'research_tracking/runs/full-project-handoff-audit-20261118-01/REQUIRED_INPUTS02.json').read_text(encoding='utf-8'))
        rows=[r for g in required['groups'] for r in g['files']]
        master=json.loads((ROOT/'research_tracking/runs/full-project-transfer-20261118-01/MANIFEST_BAN_GIAO.json').read_text(encoding='utf-8'))
        rows+=master['primary_akt_models']
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:result=list(pool.map(pin,rows))
    report=dict(status='ALL_PROTECTED_INPUT_AND_MODEL_SHA256_MATCH',files=result,count=len(result))
    (B/('PROTECTED_AFTER.json' if after else 'PROTECTED_BEFORE.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('PROTECTED',len(result),'SHA256 verified','AFTER' if after else 'BEFORE',flush=True)

if __name__=='__main__':main()
