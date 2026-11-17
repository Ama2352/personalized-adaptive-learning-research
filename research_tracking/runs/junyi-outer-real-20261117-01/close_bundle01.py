"""Đóng inventory file nhỏ để commit gói đã nghiệm thu, loại cache và credentials."""
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent
allowed={'.py','.json','.md','.html','.csv','.txt','.svg','.png','.pdf'}
paths=[path for path in B.rglob('*') if path.is_file() and path.suffix.lower() in allowed
    and '__pycache__' not in path.parts and path.name not in ('FINAL_MANIFEST01.json','COMMIT_ALLOWLIST01.json','COMMIT_PATHS01.txt')]
extras=[
    'tests/akt/test_outer_primary_bootstrap.py','docs/REPOSITORY_MAP.md',
    'docs/thesis_recovery/INVESTIGATION_STATE.json','research_tracking/RESEARCH_PROGRESS.md',
    'research_tracking/reports/README.md','research_tracking/COMPUTE_BUDGET_WORKSPACE2016.json',
    'research_tracking/runs/junyi-calibration-real-20261117-01/STATE.json',
    'research_tracking/runs/junyi-calibration-real-20261117-01/LOCAL_A3_FIT_ACCEPTANCE101.json',
    'research_tracking/runs/junyi-calibration-real-20261117-01/LOCAL_A3_RAW_ACCEPTANCE101.json',
    'research_tracking/supervisor_reports/2026-11-16/01_tien_do/BAO_CAO.md',
    'research_tracking/supervisor_reports/2026-11-16/01_tien_do/BAO_CAO_NGHIEN_CUU.html',
]
paths += [ROOT/name for name in extras]
inventory=[]
for path in sorted(set(paths)):
    assert path.resolve().is_relative_to(ROOT) and not path.is_symlink() and path.stat().st_size<=2*1024**2
    relative=path.relative_to(ROOT).as_posix()
    assert '/private/' not in relative and path.suffix.lower() in allowed,relative
    raw=path.read_bytes()
    if path.suffix.lower() not in ('.png','.pdf'):
        assert not re.search(rb'ya29\.[A-Za-z0-9_-]{15}|GOCSPX-[A-Za-z0-9_-]{10}|"refresh_token"\s*:\s*"',raw),relative
    inventory.append(dict(path=relative,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
manifest=dict(status='CLOSED_VERIFIED_OUTER_FOLD4_A0_A3',scope='Expert graph, one training seed, documented late statistical-family freeze',
    acceptance='FINAL_ACCEPTANCE01.json',files=inventory,exclusions=['Datasets','Model/checkpoint binaries','Credentials','__pycache__','Temporary prediction/cache binaries'])
manifest_path=B/'FINAL_MANIFEST01.json'
assert not manifest_path.exists()
manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
commit=[item['path'] for item in inventory]+[manifest_path.relative_to(ROOT).as_posix()]
(B/'COMMIT_ALLOWLIST01.json').write_text(json.dumps(dict(status='EXACT_REVIEWED_SMALL_FILE_ALLOWLIST',files=inventory),indent=2)+'\n')
commit += [(B/'COMMIT_ALLOWLIST01.json').relative_to(ROOT).as_posix(),(B/'COMMIT_PATHS01.txt').relative_to(ROOT).as_posix()]
(B/'COMMIT_PATHS01.txt').write_text('\n'.join(commit)+'\n',encoding='utf-8')
print('REVIEWED_ALLOWLIST_FILES',len(commit),'TOTAL_BYTES',sum(item['bytes'] for item in inventory))

if __name__=='__main__':
    pass
