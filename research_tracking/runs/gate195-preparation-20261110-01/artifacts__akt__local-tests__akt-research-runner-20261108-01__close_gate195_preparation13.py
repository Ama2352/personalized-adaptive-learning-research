"""Đóng source freeze và NO-GO trước collection, không tạo Gate PASS giả."""
from pathlib import Path
import hashlib
import json

root = Path(__file__).resolve().parents[4]
prep = Path(__file__).resolve().parent
bundle = root / 'research_tracking/runs/gate195-preparation-20261110-01'
bundle.mkdir(exist_ok=False)
sha = lambda data: hashlib.sha256(data).hexdigest()
dispatch = json.loads((prep / 'gate195-collection13-dispatch/result.json').read_bytes())
assert dispatch['returncode'] == 1
error = (prep / 'gate195-collection13-dispatch/stderr.log').read_text()
assert 'fresh4GiB before collection library imports' in error
assert not (prep / 'gate-collection13').exists() and not (prep / 'gate-collection13-outer').exists()
snapshot = json.loads((prep / 'gate_source_snapshot08.json').read_bytes())
assert snapshot['source_count'] == 195 and snapshot['test_module_count'] == 91
sources = [Path(__file__)] + [prep / name for name in (
    'prepare_gate195_collection13.py', 'run_gate195_collection13_dispatch.py', 'gate195_collection13_dispatch.json',
    'gate_source_snapshot08.json', 'gate_collection08_packet.ROOT.json', 'run_gate_collection13.py',
    'prepare_gate195_controller_derivative08.py', 'gate195_controller_derivative08.json',
    'gate195_controller_derivative08.patch', 'windows_current_gate_worker04.py', 'windows_current_gate_outer05.py')]
sources += sorted(path for path in (prep / 'gate195-collection13-dispatch').iterdir() if path.is_file())
copies = []
for source in sources:
    data = source.read_bytes()
    name = '__'.join(source.relative_to(root).parts)
    (bundle / name).write_bytes(data)
    assert source.read_bytes() == data == (bundle / name).read_bytes()
    copies.append(dict(source=source.relative_to(root).as_posix(), output=name, sha256=sha(data), size_bytes=len(data)))
readme = '''# Chuẩn bị Gate195 và lần dừng trước collection

Ngày10/11/2026, API production gate2_build_hashes/test_partition xác nhận195source files và91test modules, chia ba nhóm freshprocess. Các bytes lock, bốn file upstream và năm support documents khớp pins lịch sử. Ghim snapshot08 và packet08 riêng, không sửa hồ sơ Gate183.

## Dispatch collection13

Outer chỉ đổi output namespace12→13, giữ worker12/helper/namespace proof/caps. Lượt dispatch có stdout/stderr và returncode1. Ngưỡng fresh4GiB bị vi phạm trước OUT.mkdir và trước run_owned. Không có thư mục collection13 hoặc outer13, không có GO/test body/collection IDs hoặc Gate mới. Không ghi số RAM chính xác ở thời điểm lỗi vì controller không xuất giá trị đó trước guard. Một phép đọc RAM trước dispatch có thể khác thời điểm admission do overhead và biến động hệ thống.

## Chuẩn bị tiếp tục

Worker04 chỉ đổi exact population183/85 thành195/91; outer05 chỉ trỏ worker04. Patch và SHA before/after được giữ, AST parse đạt. Chưa chạy hai derivative này. Cần collection thật mới rồi mới ghim expected JUnit IDs, full Gate và index riêng. Không dùng1913IDs từ Gate183 làm inventory của source195, không hạ4GiB hoặc tự coi71targetedtests là full Gate.

Đây là hồ sơ vận hành/source preparation với NO-GO, chưa GatePASS hoặc kết quả RQ. RAM là blocker của lượt Gate hiện tại, còn các việc phần mềm nhẹ vẫn có thể tiếp tục. Chỉ retry khi có thêm headroom hoặc thay đổi điều kiện có bằng chứng. Modal0USD, không model training, Holdout hoặc sửa dependencies global. Kế hoạch GPU07 được cập nhật; báo cáo GVHD giữ nguyên kết luận nghiên cứu.
'''
(bundle / 'README.md').write_text(readme, encoding='utf-8')
manifest = dict(kind='CLOSED_GATE195_SOURCE_PREPARATION_NO_GO', copies=copies, source_count=195, test_module_count=91,
    collection_executed=False, test_bodies_executed=False, gate_pass=False, modal_usd=0,
    guard='fresh4GiB before collection library imports', exact_available_ram_at_failure=None,
    outputs={path.name: dict(sha256=sha(path.read_bytes()), size_bytes=path.stat().st_size)
             for path in sorted(bundle.iterdir())})
(bundle / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
state_path = root / 'docs/thesis_recovery/INVESTIGATION_STATE.json'
state = json.loads(state_path.read_bytes())
state['gate195_refresh_preparation_20261110'] = dict(status='NO_GO_RAM_BEFORE_COLLECTION',
    bundle=bundle.relative_to(root).as_posix(), sources=195, test_modules=91,
    collected_ids=None, native_test_bodies=0, gate_pass=False,
    controller_derivative='AST_ONLY_NOT_EXECUTED', exact_available_ram_at_failure=None,
    next_vi='Hoàn tất shared code còn lại; khi dư headroom4GiB, collect mới rồi full Gate/index. Không dùng IDs cũ.')
state['selection_file_admission_next_batch_20261110']['next'] = [
    'Continue lightweight exclusive publication and operation/late-failure review work',
    'Do not retry Gate until sufficient new RAM headroom is observed; collect fresh IDs first',
    'Refresh Gate on final shared source before Linux/CUDA/recovery/throughput ladder']
state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
with (root / 'docs/thesis_recovery/INVESTIGATION_LOG.md').open('a', encoding='utf-8') as stream:
    stream.write('\nGate195 preparation: genuineAPI195sources/91modules frozen snapshot08/packet08. Collection13 NO-GO fresh4GiB trước OUTmkdir/run_owned,0IDs/0body; không exactRAM tại lỗi. Derivativeworker04/outer05 chỉ population/pointer, AST-only, guards/caps nguyên. Gate vẫnSTALE195, IDs1913 cũ khôngreuse. Bundle gate195-preparation-20261110-01, GPU07 cập nhật,0Modal/subagent. Tiếp tục phần nhẹ, không retry thiếu điều kiện mới.\n')
for path, link in ((root / 'docs/REPOSITORY_MAP.md', '../research_tracking/runs/gate195-preparation-20261110-01/README.md'),
                   (root / 'research_tracking/reports/README.md', '../runs/gate195-preparation-20261110-01/README.md')):
    data = path.read_bytes()
    position = data.index(b'\n') + 1
    note = ('\n## 10/11 — Gate195 đã ghim nguồn, collection bị chặn RAM\n\n[Hồ sơ vận hành](' + link +
        ') xác nhận195sources/91modules. Collection13 dừng tại fresh4GiB trước GO, chưa có IDs/tests/PASS mới. Giữ derivative AST và failure để tiếp tục khi đủ điều kiện.\n\n').encode('utf-8')
    path.write_bytes(data[:position] + note + data[position:])
with (root / '.gitattributes').open('a', encoding='utf-8') as stream:
    stream.write('\n/research_tracking/runs/gate195-preparation-20261110-01/** -text -whitespace\n')
print('Closed', bundle.relative_to(root), 'outputs', len(list(bundle.iterdir())))
