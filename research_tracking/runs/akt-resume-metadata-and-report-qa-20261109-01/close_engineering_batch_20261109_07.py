"""Lưu bằng chứng kiểm báo cáo và AKT hiện hành, không thay bundle cũ."""
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
BUNDLE = ROOT / 'research_tracking/runs/akt-resume-metadata-and-report-qa-20261109-01'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    BUNDLE.mkdir(exist_ok=False)
    inputs = [Path(__file__).resolve()]
    for name in ('graph29-metadata-collection05-owned', 'graph29-metadata-collection05',
                 'graph29-metadata-collection06-owned', 'graph29-metadata-collection06',
                 'graph29-metadata-tests06-owned', 'graph29-metadata-tests06'):
        directory = PREP / name
        if directory.exists():
            inputs.extend(p for p in directory.rglob('*') if p.is_file()
                          and p.suffix in ('.json', '.log', '.xml', '.txt')
                          and 'runtime-temp' not in p.parts)
    for name in ('witness120_desktop01.png', 'witness120_mobile01.png',
                 'check_graph29_metadata04.py', 'run_graph29_metadata04.py',
                 'graph29_metadata04_packet.json', 'GKT_NEGATIVE_SECOND_MOMENT_FIX04.md'):
        inputs.append(PREP / name)
    inventory = {str(p.relative_to(ROOT)).replace('\\', '/'): sha(p) for p in inputs}
    write(BUNDLE / 'inventory_before_copy.json', inventory)
    outputs = {}
    for source in inputs:
        relative = source.relative_to(PREP)
        target = BUNDLE / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        assert sha(target) == inventory[str(source.relative_to(ROOT)).replace('\\', '/')]
        outputs[str(relative).replace('\\', '/')] = sha(target)
    test_path = PREP / 'graph29-metadata-tests06-owned/final.json'
    result = json.loads(test_path.read_bytes()) if test_path.exists() else None
    verdict = dict(
        AKT_metadata_status=result['status'] if result else 'MISSING_TERMINAL_RESULT',
        test_counts=result.get('child_result', {}).get('counts') if result else None,
        desktop_visual='Đã xem ảnh Chặng14, bảng và văn bản rõ.',
        mobile_visual='Đo width390, document375 và table335. Ảnh component bị lệch vị trí capture, browser sau đó mất handle. Chưa nghiệm thu visual mobile.',
        preview_cleanup='Hai server sessions65470/52785 đã terminal sau Ctrl-C. Browser list chỉ còn about:blank, owned isolated tab không còn.',
        failure05='Collection05 timeout active deadline, cleanup accepted, Job0. Giữ toàn bộ failure.',
        scientific_scope='Kiểm phần mềm và trình bày, không thêm mẫu nghiên cứu, training hoặc chi phí cloud.',
    )
    write(BUNDLE / 'verdict.json', verdict)
    (BUNDLE / 'README.md').write_text(
        '# Kiểm hợp đồng AKT và trình bày báo cáo ngày09/11\n\n'
        'Collection05 chạm hạn thời gian, đã cleanup Job0. Collection06 đạt299IDs và0test bodies. '
        'Test06 được dispatch riêng sau review receipt collection và source/runtime. Kết quả terminal nằm trong verdict.json và raw receipt, không suy diễn thành native/CUDA hoặc RQ hoàn tất.\n\n'
        'Chặng14 desktop đã đọc ảnh. Mobile đã đo bố cục nhưng ảnh component lệch capture, rồi browser mất handle. '
        'Giữ ảnh gốc và chưa đóng WRITE06. Local file protocol bị chặn. Preview đầu bị socket access denied, preview sau chỉ localhost8767 hoạt động và đã tắt. '
        'Không đóng tab người dùng.\n\n'
        'GKT đã thêm guard second moment âm và kiểm AST, còn chờ native. Note nguồn giữ riêng, không tính thành test PASS. '
        'Bản copy được inventory SHA trước và so sau. Không thay bundle lịch sử.\n', encoding='utf-8')
    write(BUNDLE / 'manifest.json', dict(kind='engineering_and_report_QA',
        inputs_sha256=inventory, outputs_sha256={str(p.relative_to(BUNDLE)).replace('\\', '/'): sha(p)
        for p in BUNDLE.rglob('*') if p.is_file()}, scope=verdict))
    print(json.dumps(verdict, ensure_ascii=False))


if __name__ == '__main__':
    main()
