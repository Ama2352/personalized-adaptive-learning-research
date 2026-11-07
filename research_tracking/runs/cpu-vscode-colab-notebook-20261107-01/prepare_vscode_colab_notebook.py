"""Chuẩn bị notebook một file; không chạy kernel hoặc cloud."""
import base64
import hashlib
import json
from pathlib import Path
import shutil
import textwrap

root=Path.cwd()
path=root/'notebooks/akt_colab_synthetic.ipynb'
before=root/'artifacts/akt/local-tests/notebook-before-vscode-20261107.ipynb'
if before.exists():raise FileExistsError(before)
shutil.copyfile(path,before)
assert hashlib.sha256(before.read_bytes()).digest()==hashlib.sha256(path.read_bytes()).digest()
old=json.loads(path.read_text(encoding='utf-8'))
bundle=(root/'artifacts/akt/colab/akt-synthetic-20261107-v11.zip').read_bytes()
digest=hashlib.sha256(bundle).hexdigest()
assert digest=='0d4d59a973b4909b26837f795ead499f3b0da6375db3dd6f58096c57530a9f09'

def cell(kind,name,source,metadata=None):
    result={'cell_type':kind,'id':name,'metadata':metadata or {},'source':source.splitlines(keepends=True)}
    if kind=='code':result.update(execution_count=None,outputs=[])
    return result

intro='''# AKT — chạy Colab GPU trong VS Code

**Mở đúng file này, chọn Select Kernel → Colab → New Colab Server → GPU T4 nếu được cấp miễn phí, rồi đăng nhập Google.**
Chạy cell **01 — kiểm kết nối** trước. Khi thấy `CONNECTED_GPU`, có thể chọn **Run All** để chạy gói kiểm nhỏ đã chuẩn bị. Không cần upload ZIP nguồn: kitv11 đã nhúng trong notebook và có SHA cố định. Không chạy bằng kernel `.venv` Windows local.

Các bước sau: giải mã nguồn → tạo `.venv` riêng trên Colab → CPU portability → CUDA lifecycle → recovery → xuất ZIP kết quả. Cell CPU có cap600s; lifecycle d256/400targets/1update cap600s; recovery d32/17targets mỗi nhánh continuous5 so với2+3updates, tổng10updates, controller180s. Đây là kiểm tổng hợp, không training Junyi/CV/Holdout, không thuê Modal và không chứng minh cải thiện RQ.

**Nếu lỗi:** dừng, không bấm Run All lại. Chạy riêng cell cuối **07 — đóng gói kết quả** để giữ logs, kể cả failure. Trong thanh Colab bên trái → Contents → `/content` → nhấp phải `akt-colab-results-....zip` → Download; giữ thêm file `.sha256`. Lưu notebook có output để cung cấp thông tin kết nối. Cuối cùng dùng **Colab: Remove Server** để giải phóng runtime. Không mua compute units nếu GPU miễn phí không khả dụng.

Việc bạn kết nối kernel chưa tự cung cấp kênh điều khiển cho agent ở terminal local. Notebook đã đủ các bước để chạy tương tác trong VS Code. Chưa có lần thực thi CUDA nào được xác nhận chỉ từ việc tạo file này.
'''
connection='''# 01 — Chỉ kiểm kết nối; không train model/cài dependency.
COLAB_CONNECTION_OK = False
CPU_PORTABILITY_OK = False
CUDA_LIFECYCLE_OK = False
SETUP_OK = False
from pathlib import Path, PurePosixPath
import base64, hashlib, importlib.util, io, json, os, platform, subprocess, sys, uuid, zipfile
if sys.platform != 'linux' or not Path('/content').is_dir():
    raise RuntimeError('Sai kernel: chọn Colab GPU trên VS Code, không dùng .venv Windows local')
import torch
if not torch.cuda.is_available():
    raise RuntimeError('Đã nối Linux nhưng chưa có CUDA GPU. Chọn Colab GPU miễn phí nếu có; không chạy bước sau')
connection_report = {'status':'CONNECTED_GPU','python':sys.version,'python_executable':sys.executable,
    'platform':platform.platform(),'torch':torch.__version__,'cuda_build':torch.version.cuda,
    'gpu_name':torch.cuda.get_device_name(0),'scope':'Connection/device discovery only; no model step'}
COLAB_CONNECTION_OK = True
print(json.dumps(connection_report,ensure_ascii=False,indent=2))
'''
bootstrap_prefix='''# 02 — Kit nguồn nhúng; cell dài được thu gọn mặc định, không cần sửa.
if not globals().get('COLAB_CONNECTION_OK',False):
    raise RuntimeError('Cell01 chưa CONNECTED_GPU; không giải nén/cài đặt')
CPU_PORTABILITY_OK = False
CUDA_LIFECYCLE_OK = False
SETUP_OK = False
RUN = None
RECOVERY_RUN = None
'''
encoded=base64.b64encode(bundle).decode('ascii')
bootstrap=bootstrap_prefix+f'EXPECTED_BUNDLE_SHA256 = {digest!r}\nBUNDLE_BASE64 = (\n'
bootstrap+=''.join('    '+repr(chunk)+'\n' for chunk in textwrap.wrap(encoded,120))+')\n'
bootstrap+='''data = base64.b64decode(BUNDLE_BASE64,validate=True)
if len(data)>20*1024*1024 or hashlib.sha256(data).hexdigest()!=EXPECTED_BUNDLE_SHA256:
    raise ValueError('Kit nhúng sai SHA/size; dừng, không dùng nguồn thay thế tự động')
with zipfile.ZipFile(io.BytesIO(data)) as archive:
    names=archive.namelist()
    if len(names)!=len(set(names)) or sum(x.file_size for x in archive.infolist())>50*1024*1024:
        raise ValueError('Archive duplicate hoặc vượt50MiB expanded')
    manifest_bytes=archive.read('BUNDLE_MANIFEST.json')
    manifest=json.loads(manifest_bytes)
    if (manifest.get('schema_version'),manifest.get('scope'))!=(2,'source_and_bounded_test_fixtures'):
        raise ValueError('Sai bundle schema/scope')
    if 'scripts/akt/synthetic_recovery_probe.py' not in manifest['files']:
        raise ValueError('Kit thiếu recovery probe')
    if set(names)!=set(manifest['files'])|{'BUNDLE_MANIFEST.json'}:
        raise ValueError('Bundle thiếu/thừa file')
    verified_contents={}
    for name,expected in manifest['files'].items():
        relative=PurePosixPath(name)
        if not relative.parts or relative.is_absolute() or '..' in relative.parts or '\\\\' in name or ':' in name:
            raise ValueError('Unsafe archive path')
        content=archive.read(name)
        if hashlib.sha256(content).hexdigest()!=expected:
            raise ValueError('Source hash mismatch: '+name)
        verified_contents[name]=content
# Chỉ tạo workspace sau khi toàn bộ payload đã qua kiểm tra.
RUN_TOKEN=uuid.uuid4().hex
ROOT=Path('/content')/('kltn-synthetic-'+RUN_TOKEN)
ROOT.mkdir(exist_ok=False)
for name,content in verified_contents.items():
    destination=ROOT.joinpath(*PurePosixPath(name).parts)
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_bytes(content)
OUTPUT=ROOT/'colab-evidence'
OUTPUT.mkdir()
(OUTPUT/'BUNDLE_MANIFEST.json').write_bytes(manifest_bytes)
(OUTPUT/'BUNDLE_SHA256.txt').write_text(EXPECTED_BUNDLE_SHA256+'\\n')
(OUTPUT/'connection.json').write_text(json.dumps(connection_report,ensure_ascii=False,indent=2)+'\\n')
print('SOURCE_READY',len(verified_contents),'files; workspace:',ROOT)
del verified_contents
'''
setup='''# 03 — Chỉ cài thiếu vào ROOT/.venv, không cài vào Python global.
SETUP_OK = False
CPU_PORTABILITY_OK = False
CUDA_LIFECYCLE_OK = False
if not globals().get('COLAB_CONNECTION_OK',False) or 'OUTPUT' not in globals():
    raise RuntimeError('Chạy cell01/02 trước')
with (OUTPUT/'setup-started.json').open('x') as stream:
    json.dump({'status':'STARTED','scope':'venv and pinned upstream preparation only'},stream)
def setup_command(label,command,timeout):
    print('Chuẩn bị:',label,flush=True)
    with (OUTPUT/('setup-'+label+'.log')).open('xb') as log:
        result=subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=timeout)
    result.check_returncode()
try:
    setup_command('venv',[sys.executable,'-m','venv','--system-site-packages',str(ROOT/'.venv')],120)
    AKT_PY=str(ROOT/'.venv/bin/python')
    packages={'numpy':'numpy','pandas':'pandas','duckdb':'duckdb','sklearn':'scikit-learn',
              'psutil':'psutil','pytest':'pytest','networkx':'networkx'}
    probe='import importlib.util,json; print(json.dumps([p for m,p in '+repr(packages)+'.items() if importlib.util.find_spec(m) is None]))'
    missing=json.loads(subprocess.check_output([AKT_PY,'-c',probe],text=True,timeout=30))
    (OUTPUT/'missing-packages.json').write_text(json.dumps(missing,indent=2))
    if missing:setup_command('packages',[AKT_PY,'-m','pip','install',*missing],300)
    upstream=ROOT/'artifacts/akt/dependencies/upstream'
    upstream.parent.mkdir(parents=True,exist_ok=True)
    setup_command('clone',['git','clone','--no-checkout','https://github.com/arghosh/AKT.git',str(upstream)],180)
    setup_command('pin',['git','-C',str(upstream),'checkout','--detach','01b7e8d7d7c862cabc9467108e3e7f2555653a88'],60)
    setup_command('freeze',[AKT_PY,'-m','pip','freeze'],60)
    ENV=dict(os.environ,PYTHONPATH=str(ROOT/'src'),PYTHONDONTWRITEBYTECODE='1')
    SETUP_OK=True
    (OUTPUT/'setup-status.json').write_text(json.dumps({'status':'READY','python':AKT_PY,
        'runtime_packages_inherited':True,'global_install':False},indent=2))
except BaseException as error:
    (OUTPUT/'setup-status.json').write_text(json.dumps({'status':'FAILED','error_type':type(error).__name__,
        'error':str(error)},ensure_ascii=False,indent=2))
    raise
print('SETUP_READY; bước kế tiếp kiểm CPU portability')
'''
cpu=''.join(old['cells'][3]['source'])
cpu=cpu.replace('CPU_PORTABILITY_OK = False','CPU_PORTABILITY_OK = False\nif not globals().get("SETUP_OK",False):\n    raise RuntimeError("Setup chưa READY; không chạy CPU suite")',1)
export='''# 07 — Đóng gói cả failure. Không cần google.colab.files hoặc trình duyệt.
if 'OUTPUT' not in globals() or not OUTPUT.is_dir():
    raise RuntimeError('Chưa có workspace; giữ output lỗi trong notebook, kiểm cell01/02')
archive_path=Path('/content')/('akt-colab-results-'+RUN_TOKEN+'.zip')
def file_sha(path):
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):digest.update(chunk)
    return digest.hexdigest()
entries={}
for directory,prefix in [(OUTPUT,''),(globals().get('RUN'),'synthetic-run/'),
                         (globals().get('RECOVERY_RUN'),'synthetic-recovery/')]:
    if directory is not None and directory.is_dir():
        for path in sorted(directory.rglob('*')):
            if path.is_file():
                if path.is_symlink():raise ValueError('Không export symlink')
                name=prefix+path.relative_to(directory).as_posix()
                if name in entries:raise ValueError('Trùng output ZIP path')
                entries[name]=(path,file_sha(path))
result_manifest={'schema_version':1,'bundle_sha256':EXPECTED_BUNDLE_SHA256,
    'cpu_portability_pass':globals().get('CPU_PORTABILITY_OK',False),
    'cuda_lifecycle_pass':globals().get('CUDA_LIFECYCLE_OK',False),
    'scope':'Bounded synthetic checks only; includes failure logs; not Gate4 or full training',
    'files':{name:digest for name,(path,digest) in entries.items()}}
with zipfile.ZipFile(archive_path,'x',compression=zipfile.ZIP_DEFLATED) as archive:
    for name,(path,expected) in entries.items():
        archive.write(path,name)
        if file_sha(path)!=expected:raise ValueError('Output đổi trong lúc export: '+name)
    archive.writestr('RESULT_MANIFEST.json',json.dumps(result_manifest,ensure_ascii=False,indent=2)+'\\n')
archive_sha=file_sha(archive_path)
archive_path.with_suffix('.zip.sha256').write_text(archive_sha+'  '+archive_path.name+'\\n')
print('RESULT_ZIP:',archive_path)
print('SHA256:',archive_sha)
print('VS Code → Colab → Contents → /content → nhấp phải ZIP và file .sha256 → Download')
print('Tải xong: dùng Colab: Remove Server để giải phóng runtime')
'''
cells=[cell('markdown','akt-instructions',intro),cell('code','akt-connection',connection),
       cell('code','akt-bootstrap',bootstrap,{'jupyter':{'source_hidden':True}}),
       cell('code','akt-setup',setup),cell('code','akt-cpu',cpu),
       cell('code','akt-lifecycle',''.join(old['cells'][4]['source'])),
       cell('code','akt-recovery',''.join(old['cells'][5]['source'])),cell('code','akt-export',export)]
notebook={**old,'cells':cells}
notebook['metadata']['kltn']={'embedded_source_bundle':'akt-synthetic-20261107-v11.zip','bundle_sha256':digest,
    'scope':'VSCode/Colab synthetic handoff; no verified remote execution'}
path.write_text(json.dumps(notebook,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
print(json.dumps({'notebook':str(path),'cells':len(cells),'embedded_bytes':len(bundle),
                  'notebook_bytes':path.stat().st_size,'bundle_sha256':digest,'remote_execution':False}))
