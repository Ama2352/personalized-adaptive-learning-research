"""Dựng notebook CPU tự chứa source launcher, không kèm credentials/binary."""
import base64
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
MAIN = ROOT / 'research_tracking/runs/junyi-calibration-real-20261117-01'


def build():
    files = {name: (ROOT / 'scripts/akt' / name).read_text(encoding='utf-8') for name in (
        'free_cpu_calibration.py', 'drive_resumable_upload.py',
        'modal_calibration_input_stage.py', 'calibration_audit_transaction.py')}
    payload = {'requests': {}, 'gpu': {}, 'numeric': {}}
    for variant in ('A2', 'A3'):
        payload['requests'][variant] = json.loads((MAIN / f'REQUEST_{variant}_GPU01.json').read_text())
        payload['gpu'][variant] = json.loads((MAIN / f'{variant}_GPU_RESULT01.json').read_text())['result']
        payload['numeric'][variant] = json.loads((MAIN / f'{variant}_NUMERIC_DRIVE_BACKUP01.json').read_text())
    payload['cache'] = json.loads((MAIN / 'CPU_CACHE_RESULT02.json').read_text())['result']
    payload['window_metadata'] = json.loads((MAIN / 'FREE_CPU_WINDOW_METADATA_DRIVE01.json').read_text())['files']
    payload['input'] = dict(file_id='1GlPhrWOLwFNeUiv1unYaEATypWmV9_Vy', bytes=134525060,
        sha256='a34cee8e961baf7056e8f16159d2b9a25afcca72f3c19b3a37bd0d711aab2d6a')
    upstream = (ROOT / 'artifacts/akt/dependencies/upstream/akt.py').read_bytes().replace(b'\r\n', b'\n')
    assert hashlib.sha256(upstream).hexdigest() == 'ace9e4486ea6d8f8c52310a8ddf27212022136eda719c12d8204fab1bfcfdc67'
    cells = []
    def markdown(text):
        cells.append(dict(id=f'calibration-cpu-{len(cells):02d}', cell_type='markdown', metadata={}, source=text.splitlines(keepends=True)))
    def code(text):
        cells.append(dict(id=f'calibration-cpu-{len(cells):02d}', cell_type='code', metadata={}, execution_count=None, outputs=[], source=text.splitlines(keepends=True)))
    markdown('''# Calibration Junyi A2/A3 trên CPU miễn phí

Notebook nối các dự đoán GPU đã có với nhãn calibration, audit đủ1.621.484target/15.847người học rồi fit temperature V1. Không training, không GPU, không Modal compute, không Holdout. Source/split/checkpoint giữ pin từ lượt17/11.

Chọn runtime CPU. Đăng nhập Drive Sang khi được hỏi. Output nghiên cứu được upload vào thư mục KLTN đã chốt và kiểm SHA. State chứa URI upload được giữ riêng trong `MyDrive/KLTN_AKT_PRIVATE/calibration-free-cpu-20261117-01`, không chia sẻ thư mục này. Binary chỉ tải về scratch Colab, không tải về máy cá nhân.

Sau khi raw đã audit và upload đủ, notebook tiếp tục được từ raw trên Drive khi runtime mất. Nếu dừng trước checkpoint raw, lần tiếp theo có thể phải nối raw lại từ dự đoán đã lưu, không chạy lại GPU. Fit bị ngắt chạy lại V1 từ raw. Chưa có số đo thời gian đầy đủ trên Colab.''')
    code('''from google.colab import auth, drive
auth.authenticate_user()
drive.mount('/content/drive')
''')
    bootstrap = 'import json,sys,base64,subprocess,venv,os\nfrom pathlib import Path\n'
    bootstrap += 'TOOLS=Path("/content/kltn-free-cpu-tools"); TOOLS.mkdir(exist_ok=True)\n'
    bootstrap += 'FILES=' + repr(files) + '\n'
    bootstrap += 'for name,text in FILES.items():\n    (TOOLS/name).write_text(text,encoding="utf-8")\n'
    bootstrap += 'PAYLOAD=' + repr(payload) + '\n'
    bootstrap += '(TOOLS/"PLAN.json").write_text(json.dumps(PAYLOAD),encoding="utf-8")\n'
    bootstrap += 'sys.path.insert(0,str(TOOLS))\nfrom free_cpu_calibration import download,VOLUME,sha\n'
    bootstrap += '''import google.auth
from google.auth.transport.requests import AuthorizedSession
credentials,_=google.auth.default(scopes=['https://www.googleapis.com/auth/drive'])
with AuthorizedSession(credentials) as session:
    account=session.get('https://www.googleapis.com/drive/v3/about',params={'fields':'user(emailAddress)'},timeout=60).json()
    assert account['user']['emailAddress']=='honguyenminhsang2005@gmail.com'
    archive=download(session,PAYLOAD['input'],Path('/content/kltn-free-cpu-input/INPUT.zip'))
from modal_calibration_input_stage import extract_verified_input
SOURCE=VOLUME/'calibration-inputs-20261117-01/source'
if not SOURCE.exists():
    extract_verified_input(archive,SOURCE)
else:
    import zipfile
    with zipfile.ZipFile(archive) as zipped:
        frozen=json.loads(zipped.read('CLOUD_INPUT_PLAN.json'))
    for pin in frozen['files']:
        target=SOURCE/pin['path']
        assert target.is_file() and target.stat().st_size==pin['bytes'] and sha(target)==pin['sha256']
'''
    bootstrap += 'upstream=SOURCE/"artifacts/akt/dependencies/upstream/akt.py"\nupstream.parent.mkdir(parents=True,exist_ok=True)\n'
    bootstrap += 'upstream.write_bytes(base64.b64decode(' + repr(base64.b64encode(upstream).decode()) + '))\n'
    bootstrap += '''venv_path=SOURCE/'.venv'
if not (venv_path/'bin/python').exists():
    venv.EnvBuilder(with_pip=False).create(venv_path)
PYTHON=str(venv_path/'bin/python')
import shutil
UV=shutil.which('uv')
assert UV, 'PREINSTALLED_UV_REQUIRED'
env=dict(os.environ,UV_CACHE_DIR=str(SOURCE/'artifacts/akt/uv-cache'))
subprocess.run([UV,'pip','install','--python',PYTHON,'numpy==2.5.4','pandas==3.0.6','duckdb==1.5.6','psutil==7.2.2','requests==2.34.2','google-auth==2.62.1','scikit-learn==1.9.1','scipy==1.18.1','pyarrow==26.0.1'],env=env,check=True)
assert not Path('/artifacts').exists() or Path('/artifacts').resolve()==VOLUME
if not Path('/artifacts').exists():
    Path('/artifacts').symlink_to(VOLUME,target_is_directory=True)
print('CPU_SOURCE_AND_VENV_PREPARED')
'''
    code(bootstrap)
    runner = '''import json,sys,os
from pathlib import Path
TOOLS=Path('/content/kltn-free-cpu-tools')
sys.path.insert(0,str(TOOLS))
from free_cpu_calibration import VOLUME,RUN,download,extract_numeric,run_variant,sha,need
SOURCE=VOLUME/'calibration-inputs-20261117-01/source'
sys.path.insert(0,str(SOURCE/'src'))
import psutil,google.auth
from google.auth.transport.requests import AuthorizedSession
from knowledge_tracing.akt.research_junyi_calibration import inference_source_identity
plan=json.loads((TOOLS/'PLAN.json').read_text())
need(inference_source_identity()==plan['requests']['A2']['source_identity'],'Frozen source mismatch')
need('torch' not in sys.modules,'CPU launcher unexpectedly imported Torch')
need(psutil.virtual_memory().available>=4*1024**3,'CPU free RAM below estimated 4GiB working budget')
state_root=Path('/content/drive/MyDrive/KLTN_AKT_PRIVATE/calibration-free-cpu-20261117-01')
state_root.mkdir(parents=True,exist_ok=True)
credentials,_=google.auth.default(scopes=['https://www.googleapis.com/auth/drive'])
with AuthorizedSession(credentials) as session:
    account=session.get('https://www.googleapis.com/drive/v3/about',params={'fields':'user(emailAddress)'},timeout=60).json()
    need(account['user']['emailAddress']=='honguyenminhsang2005@gmail.com','Drive account mismatch')
    private=session.get('https://www.googleapis.com/drive/v3/files',params={'q':"'root' in parents and name='KLTN_AKT_PRIVATE' and trashed=false",'fields':'files(id,shared,mimeType)'},timeout=60)
    need(private.status_code==200,'Private state folder lookup failed')
    private_folders=private.json().get('files',[])
    need(len(private_folders)==1 and not private_folders[0].get('shared',True),'Private state folder must be unshared MyDrive folder')
    windows=plan['cache']['windows']
    for pin in plan['window_metadata']:
        target=Path(windows['path'])/'manifest.json' if pin['path']=='WINDOW_MANIFEST.json' else Path(windows['admission_path'])
        download(session,pin,target)
    for variant in ('A2','A3'):
        archive=download(session,plan['numeric'][variant],Path('/content/kltn-free-cpu-input')/(variant+'_NUMERIC.zip'))
        extract_numeric(archive,plan['numeric'][variant],VOLUME,variant)
        print(variant,'CPU_JOIN_AUDIT_FIT_START',flush=True)
        from drive_resumable_upload import single_writer
        with single_writer(state_root/(variant+'.lock')):
            result=run_variant(plan['requests'][variant],plan['gpu'][variant],plan['cache'],session,state_root)
        print(variant,'DRIVE_CALIBRATION_COMPLETE',result['fit_verified'],flush=True)
        temperature=next(p for p in result['fit_publication']['files'] if p['path']=='fit/temperature.json')
        response=session.get('https://www.googleapis.com/drive/v3/files/'+temperature['file_id'],params={'alt':'media'},timeout=60)
        import hashlib
        need(response.status_code==200 and len(response.content)==temperature['bytes'] and hashlib.sha256(response.content).hexdigest()==temperature['sha256'],'Temperature readback mismatch')
        summary=response.json()
        print(json.dumps({k:summary[k] for k in ('total_targets','supported_targets','temperature','raw_log_loss','calibrated_log_loss','partition_sha256')},sort_keys=True),flush=True)
'''
    code('(TOOLS/"RUN_CPU.py").write_text(' + repr(runner) + ',encoding="utf-8")\nsubprocess.run([PYTHON,"-B",str(TOOLS/"RUN_CPU.py")],check=True)\n')
    markdown('''## Checkpoint vận hành

Mỗi variant chỉ được ghi hoàn tất khi đủ raw đã audit, temperature/manifest/config/resource/COMPLETE và SHA Drive được đọc lại. Đây là calibration fit, kết quả độc lập outer-fold vẫn còn bước khác. Khi lỗi, giữ state và scratch, sửa kết nối rồi chạy lại ô cuối. Không bấm tạo runtime mới nếu chỉ mất mạng. Nếu runtime bị cấp lại, chạy lại từ đầu để tải input đã pin và tiếp tục từ raw đã publish.

Runtime này không giữ GPU cần trả. Khi hoàn tất, kiểm receipt trên Drive trước khi ngắt runtime CPU. Notebook không xóa bất kỳ model/checkpoint nguồn nào.''')
    notebook = dict(nbformat=4, nbformat_minor=5, metadata={'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'}, 'language_info': {'name':'python'}}, cells=cells)
    path = ROOT / 'notebooks/akt_colab_response_calibration_cpu.ipynb'
    path.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(path)


if __name__ == '__main__':
    build()
