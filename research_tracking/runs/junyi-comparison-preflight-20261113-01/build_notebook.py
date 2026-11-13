"""Tạo notebook kiểm Colab T4, dùng nguồn đã inventory và venv riêng."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
bundle = ROOT/'artifacts/akt/colab/junyi-comparison-preflight-20261113-03.zip'
digest = hashlib.sha256(bundle.read_bytes()).hexdigest()
cells = []


def cell(kind, source):
    value = dict(cell_type=kind,metadata={},source=source.splitlines(keepends=True))
    if kind == 'code':
        value.update(execution_count=None,outputs=[])
    cells.append(value)


cell('markdown', '''# Kiểm pipeline Junyi trước training A1–A3

Notebook dùng T4 miễn phí và dữ liệu tổng hợp. Mục tiêu là kiểm nguồn, nhân quả, graph-off, batch128, checkpoint và phục hồi A0/A1. A2/A3 Junyi còn cần confidence fitted theo đúng train80 và lượt kiểm riêng.

Chọn T4 GPU trước khi chạy. Kết quả kỹ thuật cần được tải về ổ D và nghiệm thu cùng audit dữ liệu local. Notebook dùng `.venv` bên trong thư mục dự án trên Colab.
''')
cell('code', f'''from pathlib import Path
import hashlib, json, os, subprocess, sys, zipfile
from google.colab import files

EXPECTED_SHA = '{digest}'
PROJECT = Path('/content/KLTN-junyi-comparison-20261113-01')
if PROJECT.exists():
    raise RuntimeError('Thư mục lượt kiểm đã tồn tại. Giữ kết quả cũ và dùng phiên mới để tránh ghi đè.')
uploaded = files.upload()
if len(uploaded) != 1:
    raise RuntimeError('Chọn đúng một ZIP nguồn junyi-comparison-preflight-20261113-03.zip')
payload = next(iter(uploaded.values()))
assert hashlib.sha256(payload).hexdigest() == EXPECTED_SHA, 'SHA gói nguồn sai'
import io
with zipfile.ZipFile(io.BytesIO(payload)) as archive:
    for name in archive.namelist():
        target = (PROJECT/name).resolve()
        assert target.is_relative_to(PROJECT.resolve()), 'Đường dẫn ZIP ngoài dự án'
    archive.extractall(PROJECT)
manifest = json.loads((PROJECT/'BUNDLE_MANIFEST.json').read_text())
for name, expected in manifest['files'].items():
    assert hashlib.sha256((PROJECT/name).read_bytes()).hexdigest() == expected, name
print(json.dumps({{'source_files_verified':len(manifest['files']), 'bundle_sha256':EXPECTED_SHA}}))
''')
cell('code', '''subprocess.run([sys.executable,'-m','venv','--without-pip','--system-site-packages',str(PROJECT/'.venv')],check=True,timeout=60)
PYTHON = PROJECT/'.venv/bin/python'
env = dict(os.environ,PYTHONPATH=str(PROJECT/'src'),OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',
           CUBLAS_WORKSPACE_CONFIG=':4096:8',PYTHONDONTWRITEBYTECODE='1')
runtime = subprocess.run([str(PYTHON),'-c',
    "import json,sys,torch,numpy; print(json.dumps(dict(python=sys.version,torch=torch.__version__,numpy=numpy.__version__,cuda=torch.version.cuda,available=torch.cuda.is_available(),gpu=torch.cuda.get_device_name(0) if torch.cuda.is_available() else None)))"],
    cwd=PROJECT,env=env,check=True,capture_output=True,text=True,timeout=60)
print(runtime.stdout)
info = json.loads(runtime.stdout)
assert info['available'] and 'T4' in info['gpu'], 'Cần chọn T4 GPU miễn phí'
try:
    subprocess.run([str(PYTHON),'-c','import pytest'],check=True,capture_output=True,timeout=20)
except subprocess.CalledProcessError:
    subprocess.run([str(PYTHON),'-m','pip','install','pytest==9.1.1'],check=True,timeout=180)
upstream = PROJECT/'artifacts/akt/dependencies/upstream'
upstream.parent.mkdir(parents=True,exist_ok=True)
subprocess.run(['git','clone','--no-checkout','https://github.com/arghosh/AKT.git',str(upstream)],check=True,timeout=120)
subprocess.run(['git','-C',str(upstream),'checkout','--detach','01b7e8d7d7c862cabc9467108e3e7f2555653a88'],check=True,timeout=30)
OUTPUT = PROJECT/'experiments/akt/results/colab-comparison-20261113-01'
OUTPUT.mkdir(parents=True)
(OUTPUT/'runtime.json').write_text(runtime.stdout)
''')
cell('markdown', '''## Kiểm ranh giới dữ liệu và hành vi mô hình

Các ca kiểm dùng dữ liệu giả để chủ động đổi nhãn hiện tại, tương lai, vai trò người học và nguồn graph. Nhóm native dùng mô hình CPU thật để kiểm logic và phục hồi. Bước T4 tiếp theo xác nhận CUDA thực.
''')
cell('code', '''TESTS_ACCEPTED = False
(PROJECT/'artifacts/akt/local-tests').mkdir(parents=True,exist_ok=True)
attempt = len(list(OUTPUT.glob('test-attempt-*.log'))) + 1
test_log = OUTPUT/f'test-attempt-{attempt:02d}.log'
test_xml = OUTPUT/f'test-attempt-{attempt:02d}.xml'
test_files = [
    'tests/akt/test_comparison_contract.py','tests/akt/test_junyi_research_roles.py',
    'tests/akt/test_junyi_graph.py','tests/akt/test_junyi_batch128.py',
    'tests/akt/test_junyi_graph_model.py','tests/akt/test_junyi_selected_runner.py',
    'tests/akt/test_junyi_encoding_lineage.py','tests/akt/test_junyi_phase_data.py']
with test_log.open('x') as log:
    result = subprocess.run([str(PYTHON),'-B','-m','pytest','-q','-p','no:cacheprovider',
        *test_files,'--maxfail=1','--basetemp=artifacts/akt/local-tests/colab-comparison',
        '--junitxml='+str(test_xml)],cwd=PROJECT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=300)
print(test_log.read_text()[-5000:])
assert result.returncode == 0, 'Giữ log lỗi và dừng trước kiểm GPU'
TESTS_ACCEPTED = True
''')
cell('code', '''assert globals().get('TESTS_ACCEPTED') is True, 'Cần nghiệm thu bộ kiểm CPU trước'
gpu_attempt = len(list(OUTPUT.glob('gpu-attempt-*.log'))) + 1
GPU_OUTPUT = PROJECT/f'experiments/akt/results/colab-junyi-a0-a1-t4-20261113-{gpu_attempt:02d}'
gpu_log = OUTPUT/f'gpu-attempt-{gpu_attempt:02d}.log'
with gpu_log.open('x') as log:
    result = subprocess.run([str(PYTHON),'-B','scripts/akt/synthetic_junyi_comparison_probe.py',
        '--output',str(GPU_OUTPUT)],cwd=PROJECT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=300)
print(gpu_log.read_text()[-5000:])
assert result.returncode == 0, 'Giữ failure, tải artifact bằng cell cuối, không chuyển sang Modal'
receipt = json.loads((GPU_OUTPUT/'result.json').read_text())
assert receipt['status'] == 'PASS_SYNTHETIC_A0_A1_T4_BATCH128'
print(json.dumps(receipt,ensure_ascii=False,indent=2))
''')
cell('markdown', '''## Lưu bằng chứng về máy

Cell này dùng được cả khi lượt kiểm báo lỗi. Giữ ZIP trên ổ D để đối chiếu file, môi trường và kết quả. Lượt kiểm đạt A0/A1 vẫn cần được bổ sung bằng kiểm A2/A3 Junyi sau khi có confidence, cùng kiểm target từ dữ liệu thật trước training chính.
''')
cell('code', '''inventory = {}
paths = []
for directory in [OUTPUT,*sorted((PROJECT/'experiments/akt/results').glob('colab-junyi-a0-a1-t4-*'))]:
    if directory.exists():
        for path in sorted(directory.rglob('*')):
            if path.is_file():
                relative = path.relative_to(PROJECT).as_posix()
                inventory[relative] = dict(bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
                paths.append(path)
archive_path = PROJECT/'comparison-evidence.zip'
with zipfile.ZipFile(archive_path,'x',zipfile.ZIP_DEFLATED) as archive:
    for path in paths:
        archive.write(path,path.relative_to(PROJECT).as_posix())
    archive.writestr('INVENTORY.json',json.dumps(inventory,indent=2))
print(json.dumps(dict(archive_bytes=archive_path.stat().st_size,archive_sha256=hashlib.sha256(archive_path.read_bytes()).hexdigest(),files=len(paths))))
files.download(str(archive_path))
''')
notebook = dict(cells=cells,metadata=dict(kernelspec=dict(display_name='Python 3',language='python',name='python3'),
    language_info=dict(name='python'),colab=dict(name='akt_colab_junyi_comparison.ipynb')),nbformat=4,nbformat_minor=5)
destination = ROOT/'notebooks/akt_colab_junyi_comparison.ipynb'
destination.write_text(json.dumps(notebook,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for index, item in enumerate(cells):
    if item['cell_type'] == 'code':
        compile(''.join(item['source']),f'cell-{index}','exec')
print(json.dumps(dict(path=str(destination),cells=len(cells),compiled=True)))
