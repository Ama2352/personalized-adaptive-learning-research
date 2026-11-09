"""Kiểm hash ZIP/metadata và đóng hồ sơ nhỏ, không chạy notebook hoặc reader lần nữa."""
from pathlib import Path, PurePosixPath
import ast
import hashlib
import json
import os
import shutil
import sys
import time
import zipfile

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
KIT = PREP / 'main-source-data-kit01'
SYNC = PREP / 'main-source-data-notebook-sync01'
SNAP = PREP / 'main-source-data-notebook-before-sync01'
RUN = ROOT / 'research_tracking/runs/akt-main-source-data-preflight-20261110-01'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def raw(path, cap=262144):
    need(path.is_relative_to(ROOT) and path.resolve() == path and path.is_file()
         and not path.is_symlink() and path.stat().st_size <= cap, 'Bounded physical source')
    return path.read_bytes()


def pin(path, cap=262144):
    content = raw(path, cap)
    return dict(sha256=hashlib.sha256(content).hexdigest(), bytes=len(content))


def read(path):
    return json.loads(raw(path))


def write(name, value):
    with (RUN / name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


started = time.monotonic()
need(sys.dont_write_bytecode and Path(sys.prefix).resolve() == ROOT / '.venv', 'Repository .venv -B')
need(not RUN.exists(), 'Exclusive bundle')
result = read(KIT / 'result.json')
manifest = read(KIT / 'package_manifest.json')
inputs = read(KIT / 'input_inventory_before_package.json')
mismatch = read(KIT / 'default_profile_mismatch_and_resolution.json')
need(result['accepted'] is True and result['returncode'] == 0 and result['source_members'] == 283
     and result['training_or_device_authority'] is False, 'Actual Windows package acceptance')
expected = {
    'grade10-development-lifecycle01-20261108': {
        'train': dict(learners=48, targets=10080), 'selection': dict(learners=6, targets=1260),
        'calibration': dict(learners=6, targets=1260)},
    'grade10-main-lifecycle-engineering10x84-20261109-01': {
        'train': dict(learners=8, targets=672), 'selection': dict(learners=1, targets=84),
        'calibration': dict(learners=1, targets=84)}}
actual_stdout = json.loads(raw(KIT / 'stdout.log'))
need(actual_stdout == result['relocated_data_check'] and actual_stdout['accepted'] is True
     and actual_stdout['results'] == expected and raw(KIT / 'stderr.log') == b'', 'Stored Windows cold reader scope')
need(manifest['files'] == inputs and len(inputs) == 283 and manifest['schema_version'] == 3
     and manifest['neural_training_authorized'] is False
     and manifest['runtime_or_Linux_CUDA_verified'] is False, 'Closed input inventory')
zip_path = ROOT / result['package_path']
zip_before = pin(zip_path, 8 * 1024**2)
need(zip_before == dict(sha256='1eb5b613950cfc26d05f2790534ba42ece5c078ca95a9a5f91a0e6a1adbd0afc', bytes=1127266)
     and result['package_sha256'] == zip_before['sha256'] and result['package_bytes'] == zip_before['bytes'], 'Exact actual ZIP')
members = {}
with zipfile.ZipFile(zip_path) as archive:
    infos = archive.infolist()
    need(len(infos) == len({item.filename for item in infos}) == 284
         and sum(item.file_size for item in infos) <= 16 * 1024**2, 'Exact bounded package members')
    need(json.loads(archive.read('MAIN_DATA_PACKAGE_MANIFEST.json')) == manifest, 'Embedded manifest exact')
    for item in infos:
        name = item.filename
        path = PurePosixPath(name)
        need('\\' not in name and not path.is_absolute() and '..' not in path.parts
             and (item.external_attr >> 16) & 0o170000 != 0o120000
             and item.file_size <= 2 * 1024**2, 'No unsafe ZIP member')
        content = archive.read(item)  # zipfile đồng thời kiểm CRC.
        digest = hashlib.sha256(content).hexdigest()
        if name != 'MAIN_DATA_PACKAGE_MANIFEST.json':
            need(inputs[name] == digest, 'All 283 member SHA readback')
        members[name] = dict(sha256=digest, bytes=len(content), copied=False)
    original = archive.read(mismatch['path'])
    need(hashlib.sha256(original).hexdigest() == mismatch['original_sha256']
         == result['original_notebook_sha256']
         and mismatch['original_sha256'] != mismatch['default_synthetic_copy_sha256']
         and mismatch['original_output_blocks'] == 0
         and all(not cell.get('outputs') for cell in json.loads(original)['cells']), 'Paper2 original dependency preserved')
    for corpus in manifest['corpora']:
        name = f'artifacts/simulator/corpora/{corpus}/corpus.json'
        for source, digest in json.loads(archive.read(name))['source_inventory'].items():
            need(members[source]['sha256'] == digest, 'Corpus source identity uses original source bytes')
need(sum(name.startswith('artifacts/simulator/corpora/') for name in inputs) == 20
     and all('/oracle' not in name and '/authorizations/' not in name for name in inputs), 'Public data members only')
notebook = ROOT / 'notebooks/akt_colab_main_data_preflight.ipynb'
notebook_before = pin(notebook)
need(notebook_before['sha256'] == '8897540484140fc08c51417926110de9aa5cce2f50b093bc0ec34a4a8137bf07', 'Final notebook pin')
document = read(notebook)
codes = [''.join(cell['source']) for cell in document['cells'] if cell['cell_type'] == 'code']
need(len(codes) == 4 and all(not cell.get('outputs') for cell in document['cells']), 'Four unexecuted code cells')
for code in codes:
    ast.parse(code)
need('cursor.is_symlink()' in codes[1] and 'target.resolve().is_relative_to' in codes[1]
     and 'Public-data reader on this runtime only' in codes[2], 'Reviewed ancestor guards and runtime wording')
sync = read(SYNC / 'result.json')
need(sync['render_returncode'] == sync['reproduce_returncode'] == 0
     and sync['notebook_sha256'] == notebook_before['sha256'], 'Actual stdlib generator byte reproduction')
for leaf in ('render-stdout.log', 'reproduce-stdout.log'):
    record = json.loads(raw(SYNC / leaf))
    need(record['generator_reproduces_exact_bytes'] is True and record['code_AST_pass'] is True
         and record['code_cells'] == 4 and record['actual_Colab_or_venv_creation_tested'] is False, 'No Colab execution claim')
copy = {
    'build_main_source_data_kit01.py': PREP / 'build_main_source_data_kit01.py',
    'build_colab_main_data_notebook01.py': PREP / 'build_colab_main_data_notebook01.py',
    'archive_main_source_data_kit01.py': Path(__file__).resolve(),
    'akt_colab_main_data_preflight.ipynb': notebook,
    'notebooks_README.md': ROOT / 'notebooks/README.md'}
for name in ('default_profile_mismatch_and_resolution.json', 'input_inventory_before_package.json',
             'package_manifest.json', 'result.json', 'stdout.log', 'stderr.log'):
    copy['kit__' + name] = KIT / name
for name in ('render-stdout.log', 'render-stderr.log', 'reproduce-stdout.log', 'reproduce-stderr.log', 'result.json'):
    copy['sync__' + name] = SYNC / name
for name in ('inventory-before.json', 'copy-verification.json', 'akt_colab_main_data_preflight.ipynb.before',
             'build_colab_main_data_notebook01.py.before', 'build_main_source_data_kit01.py.before'):
    copy['before_sync__' + name] = SNAP / name
before = {name: dict(source=path.relative_to(ROOT).as_posix(), **pin(path)) for name, path in copy.items()}
RUN.mkdir()
write('inventory-before-copy.json', before)
verification = {}
for name, path in copy.items():
    shutil.copyfile(path, RUN / name)
    copied, after = pin(RUN / name), pin(path)
    need(copied == after == {key: before[name][key] for key in ('sha256', 'bytes')}, 'Before/copy/after same')
    verification[name] = dict(before=before[name], copied=copied, source_after=after)
need(pin(zip_path, 8 * 1024**2) == zip_before and pin(notebook) == notebook_before, 'ZIP/notebook unchanged after copy')
write('copy-verification.json', verification)
write('zip-and-member-references.json', dict(zip_path=result['package_path'], zip=zip_before,
    member_count=284, verified_source_data_members=283, members=members, all_CRC_SHA_verified=True,
    data_members_copied=0, zip_copied=False))
write('verification.json', dict(status='VERIFIED_ARCHIVE_AND_PACKAGE_BYTES_WINDOWS_READER_ONLY',
    four_code_cells_AST_pass=True, actual_generator_exact_reproduction=True,
    actual_windows_reader_corpora=expected, actual_Linux_Colab_execution=False,
    actual_device_runtime_or_training=False, default_notebook_transform_mismatch_preserved=True,
    elapsed_seconds_before_final=time.monotonic()-started))
(RUN / 'README.md').write_text('''# Gói nguồn và public corpus cho kiểm Colab CPU

Cold public reader thực tế đã đọc hai corpus từ vị trí giải nén mới trên Windows. Corpus development có train/selection/calibration 48/6/6 người mô phỏng, tương ứng 10080/1260/1260 targets. Corpus engineering có 8/1/1, tương ứng 672/84/84. Không tạo model, optimizer hoặc đọc oracle trong phép kiểm.

Notebook có bốn ô mã được kiểm AST. Generator đã được đồng bộ với kiểm symlink tại ancestor và tái tạo đúng byte notebook cuối. Dòng scope prospective trong payload được sửa từ Windows sang runtime đang chạy. Logs Windows gốc vẫn giữ nguyên. Chưa thực thi ô notebook trên Colab/Linux hoặc tạo venv ở máy đích. Torch, Git, CUDA, checkpoint và training chưa được nghiệm thu bởi hồ sơ này.

Gói ZIP gốc 1127266 byte giữ tại artifacts/akt/colab/akt-main-source-data-20261110-01.zip. Tất cả 283 thành viên source/data và embedded manifest đã được đọc lại với CRC và SHA khớp. Hồ sơ này chỉ tham chiếu ZIP cùng các data members bằng SHA/size, không nhân đôi ZIP, corpus hoặc cây giải nén.

Default source bundler bỏ output/execution metadata và serialize notebook Paper2 nên tạo SHA khác dù bản gốc không có output. Public corpus source_inventory ràng buộc raw SHA gốc. Gói Main riêng giữ nguyên bytes notebook nguồn Paper2 để đáp ứng provenance đó. Manifest lưu biến đổi còn lại ở các notebook khác. Không sửa corpus source pins để chấp nhận bản transformed.

Các snapshot trước đồng bộ generator/notebook, logs Windows và logs render/reproduce được giữ riêng. Manifest completed xác nhận integrity đóng gói. Hướng dẫn người dùng ở notebooks/README.md, notebook kiểm dữ liệu tại notebooks/akt_colab_main_data_preflight.ipynb.
''', encoding='utf-8')
outputs = {path.name: pin(path)['sha256'] for path in RUN.iterdir() if path.is_file()}
write('manifest.json', dict(schema_version=1, status='completed', kind='source_public_data_portability_preflight',
    outputs_sha256=outputs, source_inventory_before=before, zip_reference=dict(path=result['package_path'], **zip_before),
    actual_scope='WINDOWS_RELOCATED_READER_PLUS_LOCAL_NOTEBOOK_AST_BYTE_REPRODUCTION',
    Linux_Colab_CUDA_or_fit_verified=False))
for name, digest in outputs.items():
    need(pin(RUN / name)['sha256'] == digest, 'Manifest output readback')
print(json.dumps(dict(status='VERIFIED_CLOSED_METADATA_ONLY', path=RUN.relative_to(ROOT).as_posix(),
    manifest_sha256=pin(RUN / 'manifest.json')['sha256'], outputs=len(outputs), files=len(outputs)+1,
    source_members_verified=283, zip_or_data_copied=False, elapsed_seconds=time.monotonic()-started)))
