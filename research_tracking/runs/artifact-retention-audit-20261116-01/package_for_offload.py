"""Tạo gói upload nhỏ, kiểm SHA nguồn trước/sau và từng memberZIP, giữ bản gốc."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUTPUT = ROOT / 'experiments/akt/results/artifact-offload-20261116-01'
REFIT = ROOT / 'research_tracking/runs/junyi-refit-pipeline-20261114-01'
SECRET = re.compile(rb'(?:as-[A-Za-z0-9]{20,}|hf_[A-Za-z0-9]{24,}|mcpProxyToken=[A-Za-z0-9_-]{20,})')


def sha_file(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def model_files(directories):
    files = []
    for directory in directories:
        index_path = directory / 'MODEL_INDEX.json'
        index = json.loads(index_path.read_text())
        if 'checkpoint_file' in index:
            assert sha_file(directory / index['checkpoint_file']) == index['checkpoint_sha256']
            assert sha_file(directory / 'SUPPORT.zip') == index['support_sha256']
        else:
            for entry in index['entries']:
                assert sha_file(directory / entry['destination']) == entry['sha256']
        files.extend(path for path in directory.rglob('*') if path.is_file())
    return files


def pack(name, paths, purpose, contents_note):
    path = OUTPUT / name
    assert not path.exists(), 'Gói đã tạo, cần kiểm thay vì ghi đè'
    members = {}
    for source in sorted(set(paths)):
        relative = source.relative_to(ROOT).as_posix()
        assert 'private' not in source.parts and source.name not in ('.env', 'modal.toml', 'modal2016.toml')
        assert not source.is_symlink()
        if source.suffix.lower() in ('.json', '.log', '.md', '.py', '.ps1', '.xml', '.csv', '.html'):
            assert not SECRET.search(source.read_bytes()), 'Có file cần kiểm thông tin xác thực trước đónggói'
        members[relative] = dict(sha256=sha_file(source), bytes=source.stat().st_size)
    total = sum(pin['bytes'] for pin in members.values())
    assert shutil.disk_usage(ROOT).free > total + 5 * 1024**3, 'Cần giữ dự phòng5GiB'
    manifest = dict(schema='kltn-artifact-copy-v1', purpose_vi=purpose, contents_note_vi=contents_note,
                    originals_preserved=True, contains_raw_junyi_interaction_files=False,
                    metadata_may_include_learner_ids=True, files=members,
                    limits_vi='Gói lưu trữ model/provenance. Cần mã KLTN và dữ liệu đúng phiên bản để tái lập training. Chưa upload từ công cụ.')
    with zipfile.ZipFile(path, 'x', zipfile.ZIP_DEFLATED, compresslevel=1, allowZip64=True) as archive:
        for relative in members:
            source = ROOT / relative
            compression = zipfile.ZIP_STORED if source.suffix.lower() in ('.zip', '.npz', '.png') else zipfile.ZIP_DEFLATED
            archive.write(source, relative, compress_type=compression)
        archive.writestr('PACKAGE_MANIFEST.json', json.dumps(manifest, ensure_ascii=False, indent=2))
        archive.writestr('HUONG_DAN.md', '# Gói lưu trữ KLTN\n\n' + purpose + '\n\n' + contents_note +
            '\n\nGiữ cấu trúc đường dẫn trong ZIP. PACKAGE_MANIFEST.json cho biết file gốc vàSHA. '
            'Model dùng loader của repository KLTN, cấu hình và mapping đi kèm. '
            'SUPPORT.zip giữ đầu vào metadata cần nạp model. '
            'Bản sao này chưa thay thế nguồn gốc và chưa cấp quyền xóa local.\n')
    with zipfile.ZipFile(path) as archive:
        for relative, pin in members.items():
            with archive.open(relative) as stream:
                assert hashlib.file_digest(stream, 'sha256').hexdigest() == pin['sha256']
            assert sha_file(ROOT / relative) == pin['sha256']
    result = dict(path=path.relative_to(ROOT).as_posix(), bytes=path.stat().st_size,
                  sha256=sha_file(path), files=len(members), source_bytes=total,
                  source_and_members_verified=True, purpose_vi=purpose)
    (OUTPUT / (name + '.manifest.json')).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False), flush=True)
    return result


def main():
    OUTPUT.mkdir(exist_ok=True, parents=True)
    results = []
    refit = [ROOT / f'experiments/akt/results/model-export-a{i}-refit-20261114-01' for i in range(4)]
    selected = [ROOT / 'experiments/akt/results' / name for name in (
        'model-export-a0-batch128-20261112-01', 'model-export-a1-batch128-20261113-01',
        'model-export-a2-batch128-20261114-01', 'model-export-a3-batch128-20261114-01')]
    results.append(pack('01_JUNYI_REFIT_A0_A3.zip', model_files(refit),
        'Bốn model refit chính để calibration và đánh giá tiếp theo.',
        'A0 không đồ thị; A1 đồ thị cố định; A2 confidence cạnh; A3 confidence vàgate. Cùng expert graph/fold4. Chưa calibration/đánh giá độc lập.'))
    results.append(pack('02_JUNYI_SELECTED_A0_A3.zip', model_files(selected),
        'Bốn checkpoint selected-fit được chọn, phục vụ audit lựa chọn epoch.',
        'Giữ riêng với model refit. Gói này không bao gồm mọi epoch A0 cần đối chiếu ranking validation.'))
    results.append(pack('03_GRADE10_SELECTED_AND_LEGACY.zip', model_files([ROOT / 'experiments/akt/results/model-export-20261112-01']),
        'Bảy checkpoint Grade10 đã chọn và một A0Junyi lịch sử trong gói export gốc.',
        'Grade10 còn refit/calibration và vòng kín; A0Junyi best-so-far trong gói là lịch sử đã có bản mới thay thế. Giữ nguyên MODEL_INDEX gốc.'))
    extensions = {'.json', '.jsonl', '.md', '.py', '.ps1', '.log', '.xml', '.csv', '.svg', '.png', '.html', '.txt'}
    sources = [REFIT]
    sources.extend(ROOT / 'research_tracking/runs' / name for name in (
        'junyi-a3-selected-20261114-01', 'junyi-confidence-completion-20261114-01',
        'junyi-a1-selection-cache-20261113-01', 'akt-model-export-20261112-01'))
    files = [path for source in sources for path in source.rglob('*') if path.is_file()
             and path.suffix.lower() in extensions and path.stat().st_size < 16 * 1024**2]
    files.extend((ROOT / 'research_tracking/supervisor_reports/2026-11-15/01_tien_do').glob('BAO_CAO*'))
    results.append(pack('04_CORE_TRAINING_AUDIT.zip', files,
        'Log, cấu hình, nghiệm thu, figure và báo cáo của các đợt training chính.',
        'Giữ thất bại quan trọng và provenance. ArtifactZIP lớn của từngrun được định vị riêng trong danh mục archive, không nhân bản vào gói này.'))
    index = dict(status='UPLOAD_PACKAGES_VERIFIED_ORIGINALS_PRESERVED', packages=results,
                 total_package_bytes=sum(row['bytes'] for row in results), uploaded=False,
                 note_vi='Chọn nơi lưu/private phù hợp vì metadata có thể chứa learner IDs. Chưa upload hoặc xóa bất cứ bản gốc nào.')
    with (HERE / 'PACKAGES.json').open('x', encoding='utf-8') as stream:
        json.dump(index, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps(dict(status=index['status'], total_bytes=index['total_package_bytes'])), flush=True)


if __name__ == '__main__':
    main()
