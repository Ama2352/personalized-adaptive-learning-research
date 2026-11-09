"""Đóng full Gate183/1913 và index riêng đã qua public reader."""
import hashlib
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[4]
PREP=Path(__file__).resolve().parent
PREFLIGHT=ROOT/'artifacts/akt/preflight'
BUNDLE=ROOT/'research_tracking/runs/akt-current-gate183-20261110-01'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


outer_path=PREP/'win-current-gate-20261110-07-outer/result.json'
outer=read(outer_path)
publication_path=PREP/'gate07-main-index-publication01-owned/final.json'
publication=read(publication_path)
report_path=PREFLIGHT/'gate2-evidence-win-current-gate-20261110-07.json'
report=read(report_path)
assert outer['run_accepted'] and outer['errors']==[]
assert outer['owned_receipt']['cleanup_accepted'] and outer['owned_receipt']['job_active_after_cleanup']==0
assert publication['accepted'] and publication['errors']==[] and publication['environment_restored']
assert publication['owned_receipt']['cleanup_accepted'] and publication['owned_receipt']['job_active_after_cleanup']==0
assert report['test_result']==dict(passed=1913,failed=0,errors=0,skipped=0)
assert len(report['build_hashes'])==183 and len(report['test_module_sha256'])==85
assert publication['global_pointer_before_sha256']==publication['global_pointer_after_sha256']==sha(PREFLIGHT/'gate2-current.json')
index=PREFLIGHT/'gate2-main183-win-current-gate-20261110-07.json'
assert sha(index)==publication['index_sha256']=='dd8bd24f6a71e57e6206e56dc9c101648558e8dc7b5779abe015c221ea828fd0'
files=[]
for name in ('gate-collection12','gate-collection12-outer','win-current-gate-20261110-07-child',
             'win-current-gate-20261110-07-outer','gate07-main-index-publication01',
             'gate07-main-index-publication01-owned'):
    directory=PREP/name
    files.extend(p for p in directory.rglob('*') if p.is_file() and 'runtime-temp' not in p.parts
        and p.suffix in ('.json','.jsonl','.xml','.log') and p.stat().st_size<=2*1024**2)
names=('prepare_current_freeze07.py','gate_source_snapshot07.json','gate_collection07_packet.ROOT.json',
    'gate_collection_worker12.py','run_gate_collection12.py','prepare_windows_current_gate_packet04.py',
    'prepare_windows_current_gate_packet05.py','windows_current_gate_worker02.py','windows_current_gate_worker03.py',
    'windows_current_gate_outer03.py','windows_current_gate_outer04.py','windows_current_gate_packet06.ROOT.json',
    'windows_current_gate_packet06.ROOT.REJECTED_METADATA_PREPARATION.json','windows_current_gate_packet07.ROOT.json',
    'gate_population_derivative07_inventory.json','GATE_PACKET_POPULATION_FIX_20261110_01.md',
    'GATE_CURRENT_REFRESH_20261110_HANDOFF01.md','gate07_actual_publication_input_hashes.json',
    'publish_gate07_main_index01.py','run_publish_gate07_main_index01.py',
    'GATE07_INDEX_OUTER_HANDOFF01.md','GRAPH29_GENUINE_PUBLIC_PARITY_SCOPE_20261110.md')
files += [PREP/name for name in names]
files += list(PREFLIGHT.glob('*win-current-gate-20261110-07*'))
files += [Path(__file__).resolve()]
files=list(dict.fromkeys(p for p in files if p.is_file()))
BUNDLE.mkdir(exist_ok=False)
write(BUNDLE/'inventory_before_copy.json',{p.relative_to(ROOT).as_posix():dict(sha256=sha(p),bytes=p.stat().st_size) for p in files})
for source in files:
    relative=source.relative_to(ROOT)
    if source.is_relative_to(PREP):
        relative=Path('execution')/source.relative_to(PREP)
    target=BUNDLE/relative
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(source,target)
    assert sha(source)==sha(target)
write(BUNDLE/'acceptance.json',dict(kind='current_AKT_Windows_CPU_software_Gate',
    counts=report['test_result'],sources=183,test_modules=85,subtests_in_remaining=135,
    gate_elapsed_seconds=outer['elapsed_seconds'],publication_elapsed_seconds=publication['elapsed_seconds'],
    index_path=index.relative_to(ROOT).as_posix(),index_sha256=sha(index),
    genuine_preflight_and_public_reader=True,global_pointer_unchanged=True,
    old_metadata_packet06_rejected_before_native=True,
    full_cv_authorized=False,Holdout_access=False,Modal_spend=0,CUDA_verified=False,
    public_producer_resume_verified=False))
(BUNDLE/'README.md').write_text('# Gate nguồn hiện hành183 và public index riêng\n\n'
    'Ba nhóm freshprocess đã chạy đủ1913physicalcases,0failure/error/skip. '
    '135subtests của nhómremaining được ghi riêng. FullGate405,48s trongcap630, '
    'genuinepreflight/source/lock/upstream/physicalJUnit và ownedJob0 đều đạt. '
    'Index riêng được publicreader kiểm lại, publisher3,69s và globalpointer giữ nguyên. '
    'Collection12 giữ1913IDs/0bodies, không cộng thànhtestPASS. '
    'Metadata06 thất bại vì lớpđiềuphối còn ghim177/81, chưa dispatchnative; giữpacket vànote. '
    'Derivative chỉ cập nhật exactpopulation183/85 cùng ownrefs, dùnglạicollectionaccepted, giữguards/caps. '
    'Đây là softwareGate CPU cho tests/akt vàtests/shared_kt. ChưaCUDA, publicproducerresume, '
    'researchfit, fullCV hoặc quyền chiModal. Chưa đóngRQ hoặctoànluậnvăn.\n',encoding='utf-8')
write(BUNDLE/'manifest.json',dict(kind='current_CPU_software_gate_and_index',
    outputs_sha256={p.relative_to(BUNDLE).as_posix():sha(p) for p in BUNDLE.rglob('*') if p.is_file()}))
state_path=ROOT/'docs/thesis_recovery/INVESTIGATION_STATE.json'
state=read(state_path)
state['current_Gate_refresh_20261110'].update(status='ACTUAL1913_PASS_CURRENT183_INDEX_PUBLIC_VALIDATED',
    native_test_bodies=1913,session_status='TERMINAL_EXIT0',gate_receipt_sha256=sha(outer_path),
    index_path=index.relative_to(ROOT).as_posix(),index_sha256=sha(index),
    publication_receipt_sha256=sha(publication_path),bundle=BUNDLE.relative_to(ROOT).as_posix())
state['next_recommended_investigation']=('Root review genuinepublicA0 control metadata dry/allocation, materializeclosedauth, '
    'runcontinuouscontrol beforechoosingpause. Demo03fullHTTP/UI pending. SAKT07 isolatedcandidates inprogress. '
    'Không chiModal hoặcđổiMain/Gate source khi publicparity đang chuẩn bị.')
write(state_path,state)
for name in ('BAO_CAO.md','BAO_CAO_NGHIEN_CUU.html'):
    path=ROOT/'research_tracking/supervisor_reports/2026-11-10/01_tien_do'/name
    text=path.read_text(encoding='utf-8')
    old='Chuẩn bị AKT đã đạt 299 kiểm hợp đồng và 18 kiểm checkpoint thật trên CPU theo nguồn hiện hành.'
    addition=(' Bộ nghiệm thu tích hợp hiện hành đã đạt 1.913 ca, bao gồm nhiều kiểm đã chạy riêng trước đó. '
        'Mốc này kiểm sự phối hợp của các thành phần trước khi dùng tài nguyên huấn luyện lớn.')
    assert text.count(old)==1
    path.write_text(text.replace(old,old+addition),encoding='utf-8')
with (ROOT/'docs/thesis_recovery/INVESTIGATION_LOG.md').open('a',encoding='utf-8') as stream:
    stream.write('\n\n## 10/11 — fullGate1913 và index riêng đã đạt\n\n'
        'Actual fullGate405,48s/1913cases0FES, remaining135subtests ghi riêng. '
        'Current183sources/85modules và3freshgroups đúngcollection. Publisher3,69s/publicreader đạtindexdd8bd24f, '
        'globalpointer nguyên. Đã giữmetadata06failureguard177/81 vàminimalderivative183/85, không recollect. '
        'Root source hiệnđủsoftwareGate, next actualpublicproducercontrol/pause/resume vẫnriêng. '
        'Hai báo cáo10/11 cập nhậtmốcnày, khôngchỉGPUTask14/Junyi CV hoặcchiModal.\n')
print('CURRENT_GATE1913_INDEX_PUBLIC_BUNDLE_CLOSED',len(files))
