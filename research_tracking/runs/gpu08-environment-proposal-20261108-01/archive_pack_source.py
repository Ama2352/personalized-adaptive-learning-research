"""Đóng archive GPU08 metadata đã có; không cài/chạy runtime hoặc kết nối mạng."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys

ROOT = Path.cwd().resolve()
if Path(sys.prefix).resolve() != ROOT / '.venv':
    raise ValueError('Chỉ dùng project .venv')
sys.path.insert(0, str(ROOT / 'src'))
from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle

# Chỉ áp dụng cho các Git read-only subprocess của lần đóng gói này.
count = int(os.environ.get('GIT_CONFIG_COUNT', '0'))
os.environ[f'GIT_CONFIG_KEY_{count}'] = 'safe.directory'
os.environ[f'GIT_CONFIG_VALUE_{count}'] = ROOT.as_posix()
os.environ['GIT_CONFIG_COUNT'] = str(count + 1)

RUN = 'gpu08-environment-proposal-20261108-01'
BASE = ROOT / 'artifacts/akt/gpu08-env-20261108-01'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


original_inventory = json.loads((BASE / 'inventory.json').read_text(encoding='utf-8'))
assert original_inventory['verified_output_count'] == 16
for row in original_inventory['files']:
    assert sha(ROOT / row['path']) == row['sha256'], row['path']
proposal = json.loads((ROOT / 'experiments/akt/configs/linux-cuda-runtime-proposal.json').read_text(encoding='utf-8'))
assert proposal['status'] == 'proposal_only' and proposal['lock_complete'] is False
assert proposal['execution_enabled'] is False
assert proposal['metadata_fetch_summary']['total_response_bytes'] == 265132

pairs = [
    (ROOT / 'docs/akt-linux-cuda-environment.md', 'akt-linux-cuda-environment.md'),
    (ROOT / 'experiments/akt/configs/linux-cuda-runtime-proposal.json', 'linux-cuda-runtime-proposal.json'),
    (ROOT / 'src/knowledge_tracing/evidence.py', 'evidence_helper_source.py'),
    (Path(__file__).resolve(), 'archive_pack_source.py'),
]
for path in sorted(BASE.iterdir()):
    assert path.is_file() and path.suffix != '.whl'
    alias = {'README.md': 'preparation_README.md', 'inventory.json': 'preparation_inventory.json'}.get(path.name, path.name)
    pairs.append((path, alias))
assert len({alias for _, alias in pairs}) == len(pairs) == 19
before = [{'source':path.relative_to(ROOT).as_posix(), 'archived_as':alias,
           'sha256_before_copy':sha(path), 'bytes':path.stat().st_size} for path, alias in pairs]
input_rechecks = [{'path':name,'historical_sha256':item['sha256'],
                   'current_sha256':sha(ROOT/name), 'match':sha(ROOT/name)==item['sha256']}
                  for name,item in original_inventory['inputs'].items()]
metadata = {
    'kind':'GPU08_LINUX_CUDA_ENVIRONMENT_PROPOSAL_ARCHIVE',
    'environment_status':'PARTIAL_PROPOSAL_ONLY', 'lock_complete':False,
    'execution_enabled':False, 'new_metadata_requests_during_archive':0,
    'new_install_model_gpu_cloud_runs':0, 'wheel_downloaded':False,
    'source_metadata_successful_http_responses':4, 'source_metadata_response_bytes':265132,
    'original_inventory_outputs_verified':16,
    'original_input_rechecks':input_rechecks,
    'scope_vi':'Archive nguyên bytes của proposal/docs/official index/PEP658/receipts; không là Linux lock/image/runtime acceptance.',
    'financial_allocation_changed':False, 'thesis_draft_included':False,
}
note = '''# GPU08: archive đề xuất môi trường Linux/CUDA — 08/11/2026

Bundle đã đóng về integrity; môi trường vẫn PARTIAL/proposal_only, execution tắt,
lock_complete=false. Không có Linux resolver closure, full transitive hash lock,
install report, image digest hoặc actual CUDA main-worker acceptance. Trạng thái
completed trong manifest chỉ là archive hoàn tất, không phải GPU08 hoàn thành.

Nguồn chính thức gồm https://pytorch.org/get-started/previous-versions/,
https://download.pytorch.org/whl/cu126/torch/ và
https://download.pytorch.org/whl/cu126/triton/; exact wheel/metadata URLs và index
SHA nằm trong proposal/candidate receipts. NVIDIA/Modal documentation URLs giữ
trong proposal và snapshot docs. Metadata bytes đã đối chiếu SHA với index;
wheel SHA chỉ là giá trị công bố, chưa kiểm wheel bytes và không tải wheel.

Giữ DNS failure fetch-01.json và cả hai lượt fetch-02/03:4responses265132bytes,
max147978bytes, cap1MiB/response/10MiBtotal. Offline validation đã có RC0/0.36s;
không chạy lại validation/model/resolver ở archive này. V12 Colab T4 dùng
Torch2.14.1+cu130 kế thừa packages không chứng nhận candidate Torch2.7.1+cu126
isolated venv hoặc current main worker. Windows pip--platform không tự chuyển
PEP508 platform_system/sys_platform; cần actual Linux/target-marker-aware resolve.

copy_inventory_before.json được ghi trước19copies; copy_inventory.json đối chiếu
SHA source/destination và giữ bytes. preparation_inventory.json là inventory
gốc; original_input_rechecks trong manifest phân biệt SHA lịch sử với file hiện
tại, không viết lại proposal nếu tài liệu vận hành về sau thay đổi. Snapshot
docs/proposal giữ links theo repository gốc; archive không là standalone runtime.

Chưa install, image build, Volume, GPU/Modal compute, cloud spend, auth hoặc thay
phân bổ tài chính. Không wheel/private credentials, raw data/Holdout hoặc thesis
draft trong bundle. Bản thảo luận văn/source map giữ ở canonical reports riêng.

record_evidence_run/verify_evidence_bundle đóng và kiểm bundle. git_ignore_check.json
ghi từng command Git check-ignore với path qua argv tường minh, không stdin;
force_add_paths.txt là danh sách chính xác bị ignore. Git chỉ được đọc, safe.directory
chỉ cấu hình ở process; không add/commit/push hoặc đổi config global/index/state.
'''
with record_evidence_run(ROOT, RUN, metadata=metadata, sources=[path for path,_ in pairs], note=note) as directory:
    (directory/'copy_inventory_before.json').write_text(json.dumps(before,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    after=[]
    for item in before:
        source=ROOT/item['source'];assert sha(source)==item['sha256_before_copy']
        destination=directory/item['archived_as']
        with destination.open('xb') as output:output.write(source.read_bytes())
        row={**item,'sha256_after_copy':sha(destination)}
        row['exact_match']=row['sha256_before_copy']==row['sha256_after_copy']
        assert row['exact_match'];after.append(row)
    (directory/'copy_inventory.json').write_text(json.dumps(after,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    planned = {'manifest.json','README.md','execution.log','copy_inventory_before.json','copy_inventory.json',
               'git_ignore_check.json','force_add_paths.txt',*(alias for _,alias in pairs)}
    ignore_checks=[];force=[]
    for name in sorted(planned):
        path=(directory/name).relative_to(ROOT).as_posix()
        command=['git','check-ignore','--no-index','--verbose','--',path]
        result=subprocess.run(command,cwd=ROOT,text=True,capture_output=True,timeout=10)
        assert result.returncode in (0,1),(command,result.stderr)
        ignored=result.returncode==0
        ignore_checks.append({'path':path,'argv':command,'returncode':result.returncode,
                              'ignored':ignored,'stdout':result.stdout.strip(),'stderr':result.stderr.strip(),
                              'stdin_used':False})
        if ignored:force.append(path)
    assert force==[f'research_tracking/runs/{RUN}/execution.log',f'research_tracking/runs/{RUN}/local-validation.log']
    (directory/'git_ignore_check.json').write_text(json.dumps(ignore_checks,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (directory/'force_add_paths.txt').write_text('\n'.join(force)+'\n',encoding='utf-8')
    assert {path.name for path in directory.iterdir()}==planned

# Bundle bất biến sau closure; từ đây chỉ đọc/verify.
verified=verify_evidence_bundle(directory)
manifest=json.loads((directory/'manifest.json').read_text(encoding='utf-8'))
assert {path.name for path in directory.iterdir()}=={'manifest.json',*manifest['outputs_sha256']}
for item in after:
    assert sha(ROOT/item['source'])==sha(directory/item['archived_as'])==item['sha256_before_copy']
print(json.dumps({'bundle':directory.relative_to(ROOT).as_posix(),'verified':verified,
    'exact_copy_pairs':len(after),'manifest_sha256':sha(directory/'manifest.json'),
    'force_add_paths':force,'thesis_draft_included':False},ensure_ascii=False,indent=2))
