"""Dựng danh mục đọc được và gói catalog từ các kết quả hash đã nghiệm thu."""
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

import audit_retention as audit


def file_sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def link(relative, label=None):
    return '[' + (label or relative) + '](<' + (audit.ROOT / relative).as_posix() + '>)'


def main():
    summary = json.loads((audit.HERE / 'SUMMARY.json').read_text())
    packages = json.loads((audit.HERE / 'PACKAGES.json').read_text())
    archives = json.loads((audit.OUTPUT / 'EXISTING_ARCHIVES_READY.json').read_text())
    with (audit.OUTPUT / 'UNUSED.csv').open(encoding='utf-8-sig', newline='') as stream:
        unused = list(csv.DictReader(stream))
    groups = defaultdict(lambda: dict(files=0, bytes=0))
    for row in unused:
        group = '/'.join(row['path'].split('/')[:3])
        groups[group]['files'] += 1
        groups[group]['bytes'] += int(row['bytes'])
    report = '# Kiểm kê checkpoint/artifact và gói lưu trữ ngày16/11/2026\n\n'
    report += '## Kết quả chính\n\n'
    report += ('Đã kiểm kê metadata ' + f'{summary["inventory_files"]:,}' + ' file trong các vùng đọc được và hash thực tế khoảng116,00GB binary. '
               'Danh mục UNUSED có ' + f'{len(unused):,}' + ' file, tổng ' + f'{summary["catalogs"]["UNUSED.csv"]["bytes"]/10**9:.2f}' + 'GB. '
               'Các con sốGB trong báo cáo dùng10^9byte. File gốc giữ nguyên. Gói nén mới là bản sao để người dùng chọn nơi upload.\n\n')
    report += '| Nhóm UNUSED | File | Dung lượng | Căn cứ |\n|---|---:|---:|---|\n'
    labels = {
        'UNUSED_VERIFIED_DUPLICATE': ('Bản local trùng nội dung', 'Cùng size/SHA thực tế; mỗi dòng chỉ rõ bản giữ ngoài UNUSED'),
        'UNUSED_VERIFIED_TRANSFER_PART': ('Phần chia upload cũ', 'Ghép tuần tự khớpSHA ZIP đầy đủ; A3 đã refit xong'),
        'UNUSED_RESUME_FINISHED_RUN': ('Checkpoint phục hồi đã hết nhiệm vụ', 'Đợt refit tương ứng đã nghiệm thu; binary lịch sử vẫn có thể giữ lạnh theo nhu cầu audit')}
    for category, (label, reason) in labels.items():
        count = summary['categories'].get(category, dict(files=0, bytes=0))
        report += f'| {label} | {count["files"]:,} | {count["bytes"]/10**9:.2f}GB | {reason} |\n'
    report += '\n## Vị trí các bản dư lớn\n\n| Vùng | File trong UNUSED | Tổng |\n|---|---:|---:|\n'
    for name, values in sorted(groups.items(), key=lambda item: -item[1]['bytes']):
        report += f'| {link(name)} | {values["files"]:,} | {values["bytes"]/10**9:.2f}GB |\n'
    report += '\nChi tiết từng file, SHA, đường dẫn bản giữ, phân loại nguồn và điều kiện xử lý tại ' + link(summary['catalogs']['UNUSED.csv']['path'], 'UNUSED.csv') + '. '
    report += ('Các snapshot/bundle đã đóng cần giữ lineage khi thu gọn, dùng relocation hoặc hướng dẫn dựng lại đúngSHA. '
               'Danh mục này phục vụ duyệt từng nhóm; các bản gốc trong thư mục hiện vẫn tồn tại.\n\n')
    report += '## Các file phải giữ cho công việc tiếp theo\n\n'
    report += ('- Bốn model refit JunyiA0–A3, MODEL_INDEX và SUPPORT.zip để calibration/đánh giá độc lập.\n'
               '- Bốn checkpoint selected-fit được chọn và các bản epochA0 còn cần đối chiếu ranking validationbatch1/128.\n'
               '- Bảy checkpointGrade10 cùngsource/mapping để hoàn thiện refit và vòng kín. Gói export gốc có thêm một A0Junyi best-so-far lịch sử.\n'
               '- Encoding, learner roles, cohort và cache nền, graph/confidence TRAIN80, source/dependency và baseline lịch sử.\n'
               '- Log, prediction và figure phục vụ các kết luận nghiên cứu; metadata của các run lỗi quan trọng.\n\n')
    report += 'Danh sách chi tiết tại ' + link(summary['catalogs']['KEEP_ACTIVE.csv']['path'], 'KEEP_ACTIVE.csv') + '.\n\n'
    report += '## Lưu trữ lạnh\n\n'
    cold = summary['catalogs']['ARCHIVE_ONLY.csv']
    report += f'{cold["files"]:,} file khoảng{cold["bytes"]/10**9:.2f}GB thuộc ARCHIVE_ONLY. '
    report += ('Đây là artifact lịch sử hoặc input snapshot, vẫn có giá trị truy vết và tái lập. '
               'Khi cần kiểm lại run cũ có thể phải tải chúng về. Các rawcheckpoint trùng đã tách khỏi nhóm này.\n\n')
    report += (f'Đã định vị{len(archives)} ZIP lớn có thể upload nguyên file, tổng{sum(row["bytes"] for row in archives)/10**9:.2f}GB. '
               'Chúng đã có SHA thực tế, giúp tránh tạo thêm một bản nén hàng chụcGB trênD. Danh sách tại ' +
               link((audit.OUTPUT / 'EXISTING_ARCHIVES_READY.json').relative_to(audit.ROOT).as_posix(), 'EXISTING_ARCHIVES_READY.json') + '.\n\n')
    report += '## Gói upload đã tạo và kiểm\n\n| Gói | Dung lượng | Nội dung |\n|---|---:|---|\n'
    for row in packages['packages']:
        report += f'| {link(row["path"], Path(row["path"]).name)} | {row["bytes"]/10**6:.1f}MB | {row["purpose_vi"]} |\n'
    report += ('\nTổng bốn gói ' + f'{packages["total_package_bytes"]/10**6:.1f}' + 'MB. '
               'Đã đối chiếuSHA nguồn trước/sau, từng member trongZIP và SHA cảZIP. Giữ cấu trúc đường dẫn khi giải nén. '
               'Các model.pt dùng loaderKLTN cùng cấu hình vàmapping; SUPPORT.zip đi kèm mỗi export. '
               'Metadata có learnerIDs và thông tin vận hành, phù hợp kho lưu trữ riêng. '
               'Gói model không chứa file tương tácJunyi gốc. Các ZIP lịch sử có thể chứa prediction/labels hoặc cohort nên cần xem nội dung khi chọn phạm vi chia sẻ.\n\n')
    report += '## Phần cần rà thêm và giới hạn\n\n'
    review = summary['catalogs']['REVIEW.csv']
    report += (f'- {review["files"]:,} file khoảng{review["bytes"]/10**9:.2f}GB ở REVIEW, phần lớn runtime/localtests; chưa đủ căn cứ kết luận unused.\n'
               '- .pytest_cache bịWindows từ chối quyền đọc trong lượt kiểm. Nó được ghi riêng trong SUMMARY, không được gán unused.\n'
               '- Vùngprivate/credentials, Holdout/Test được bỏ qua. Vùng bảo vệBKT/dataset/venv/WSL giữ nguyên.\n'
               '- SHA tập trung binary>=1MiB có cùng kích thước, model/cache đang dùng và ZIP>=100MiB. Chưa kiểm trùng toàn bộ file nhỏ.\n'
               '- ZIP khácSHA có thể chứa các member chồng lặp. Chưa suy bảnZIP nào dư hoàn toàn chỉ từ tên hoặc CRC.\n'
               '- KEEP_ACTIVE là danh mục bảo thủ cho workflow hiện hành; việc mở thí nghiệm mới có thể thay đổi phụ thuộc.\n\n')
    report += '## Cách sử dụng\n\n'
    report += ('1. Giữ model refit chính và các input đang dùng trênD trong giai đoạn calibration/đánh giá.\n'
               '2. Chọn các gói model/audit ở trên để uploadDrive hoặcHuggingFace. Sau upload cần tải kiểm đúng phiên bản/SHA trước khi đổi vị trí bản local.\n'
               '3. Với lịch sử lớn, upload từngZIP đã có theo danh mục lưu trữ lạnh.\n'
               '4. Duyệt từng nhóm UNUSED khi cần thu gọn, đối chiếu bản giữ và giữ đường dẫn manifest có thể truy vết.\n\n')
    report += 'Nguồn kiểm tại ' + link((audit.HERE / 'SUMMARY.json').relative_to(audit.ROOT).as_posix()) + ' và ' + link((audit.HERE / 'CLASSIFICATION_REVIEW.json').relative_to(audit.ROOT).as_posix()) + '.\n'
    destination = audit.ROOT / 'research_tracking/reports/ARTIFACT_RETENTION_20261116.md'
    destination.write_text(report, encoding='utf-8')
    (audit.OUTPUT / 'README.md').write_text(report, encoding='utf-8')
    unused_note = ('# Danh mục UNUSED\n\n'
        f'Có{len(unused):,} file/{summary["catalogs"]["UNUSED.csv"]["bytes"]/10**9:.2f}GB. '
        'Mở UNUSED.csv để xem đầy đủ. Cộtpath vàkeeper tính từ D:/Dev/KLTN; reason nêu căn cứ, action nêu điều kiện thu gọn. '
        'Với các bản trùng, SHA của source và keeper đã kiểm. Checkpoint phục hồi hết nhiệm vụ được tách với bản trùng. '
        'Bản gốc giữ nguyên, đề xuất dọn cần xử lý lineage snapshot và có bản lưu phù hợp.\n')
    (audit.OUTPUT / 'UNUSED.md').write_text(unused_note, encoding='utf-8')
    catalog_sources = [audit.OUTPUT / name for name in ('UNUSED.csv', 'KEEP_ACTIVE.csv', 'ARCHIVE_ONLY.csv',
        'REVIEW.csv', 'INVENTORY.jsonl', 'HASHES.jsonl', 'DUPLICATES.json', 'TRANSFER_PARTS_VERIFIED.json',
        'EXISTING_ARCHIVES_READY.json', 'UNUSED.md', 'README.md')]
    catalog_sources.extend(audit.HERE / name for name in ('SUMMARY.json', 'CLASSIFICATION_REVIEW.json', 'PACKAGES.json'))
    catalog_zip = audit.OUTPUT / '05_RETENTION_CATALOGS.zip'
    assert not catalog_zip.exists()
    pins = {}
    with zipfile.ZipFile(catalog_zip, 'x', zipfile.ZIP_DEFLATED, compresslevel=1, allowZip64=True) as archive:
        for source in catalog_sources:
            name = source.relative_to(audit.ROOT).as_posix()
            pins[name] = dict(bytes=source.stat().st_size, sha256=file_sha(source))
            archive.write(source, name)
        archive.writestr('PACKAGE_MANIFEST.json', json.dumps(pins, ensure_ascii=False, indent=2))
    with zipfile.ZipFile(catalog_zip) as archive:
        for name, pin in pins.items():
            with archive.open(name) as stream:
                assert hashlib.file_digest(stream, 'sha256').hexdigest() == pin['sha256']
            assert file_sha(audit.ROOT / name) == pin['sha256']
    result = dict(status='RETENTION_CATALOG_PACKAGE_VERIFIED', path=catalog_zip.relative_to(audit.ROOT).as_posix(),
                  bytes=catalog_zip.stat().st_size, sha256=file_sha(catalog_zip), members=len(pins),
                  all_originals_preserved=True, uploaded=False, free_bytes=shutil.disk_usage(audit.ROOT).free)
    with (audit.HERE / 'CATALOG_PACKAGE.json').open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
