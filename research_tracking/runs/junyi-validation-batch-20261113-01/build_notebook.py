"""Tạo notebook T4 đo validation batch từ bộ kiểm venv hiện có."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
source=ROOT/'artifacts/akt/colab/junyi-validation-batch-20261113-02.zip'
digest=hashlib.sha256(source.read_bytes()).hexdigest()
notebook=json.loads((ROOT/'notebooks/akt_colab_junyi_comparison.ipynb').read_text(encoding='utf-8'))
for cell in notebook['cells']:
    text=''.join(cell['source'])
    text=text.replace('KLTN-junyi-comparison-20261113-01','KLTN-validation-batch-20261113-01')
    text=text.replace('junyi-comparison-preflight-20261113-03.zip','junyi-validation-batch-20261113-02.zip')
    text=text.replace('f6722ca4a130ec5c1f40d30e9a55016d80dcaf619ed74c948f15975aac9716c4',digest)
    text=text.replace('colab-comparison-20261113-01','colab-validation-batch-20261113-01')
    cell['source']=text.splitlines(keepends=True)
notebook['cells'][0]['source']=['# Đo validation batch128 trên T4\n',
    '\nĐối chiếu dự báo từng cửa sổ và batch128 trên A0/A1 cùng dữ liệu tổng hợp. '
    'Đo thời gian, VRAM và sai lệch xác suất. Dùng venv trong dự án. '
    'Kết quả cần kiểm riêng với checkpoint A0 thật trước khi xác nhận giữ nguyên lựa chọn epoch.\n']
notebook['cells'][3]['source']=['## Kiểm nguồn và pipeline trước phép đo GPU\n',
    '\nBộ kiểm gồm target/OOV, grant, checkpoint/resume và mô hình CPU thật.\n']
code=''.join(notebook['cells'][4]['source'])
start=code.index('test_files = [')
end=code.index('\nwith test_log',start)
code=code[:start]+'''test_files = [
    'tests/akt/test_junyi_validation_batch.py','tests/akt/test_prediction_batch.py',
    'tests/akt/test_junyi_selected_runner.py','tests/akt/test_junyi_comparison_admission.py',
    'tests/akt/test_comparison_contract.py']'''+code[end:]
notebook['cells'][4]['source']=code.splitlines(keepends=True)
notebook['cells'][5]['source']='''assert globals().get('TESTS_ACCEPTED') is True
GPU_OUTPUT = PROJECT/'experiments/akt/results/colab-validation-batch-probe-20261113-01'
with (OUTPUT/'gpu-validation.log').open('x') as log:
    result = subprocess.run([str(PYTHON),'-B','scripts/akt/synthetic_validation_batch_probe.py',
        '--output',str(GPU_OUTPUT)],cwd=PROJECT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=300)
print((OUTPUT/'gpu-validation.log').read_text()[-7000:])
assert result.returncode == 0, 'Giữ failure và tải bằng chứng trước khi xử lý tiếp'
receipt = json.loads((GPU_OUTPUT/'result.json').read_text())
assert receipt['status'] == 'PASS_SYNTHETIC_VALIDATION_BATCH128_PARITY'
print(json.dumps(receipt,ensure_ascii=False,indent=2))
'''.splitlines(keepends=True)
notebook['cells'][6]['source']=['## Lưu bằng chứng\n',
    '\nTải ZIP về ổ D, kiểm SHA và inventory. Phép đo này dùng dữ liệu tổng hợp trong RAM. '
    'Thời gian SQL/I/O toàn Junyi và chọn lại epoch A0 còn cần nghiệm thu riêng.\n']
last=''.join(notebook['cells'][7]['source'])
start=last.index('for directory in ')
end=last.index('\n    if directory.exists()',start)
last=last[:start]+"for directory in [OUTPUT,PROJECT/'experiments/akt/results/colab-validation-batch-probe-20261113-01']:"+last[end:]
notebook['cells'][7]['source']=last.splitlines(keepends=True)
notebook['metadata']['colab']['name']='akt_colab_validation_batch.ipynb'
for index,cell in enumerate(notebook['cells']):
    if cell['cell_type']=='code':
        compile(''.join(cell['source']),f'cell-{index}','exec')
destination=ROOT/'notebooks/akt_colab_validation_batch.ipynb'
destination.write_text(json.dumps(notebook,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(notebook=str(destination),source_sha256=digest,compiled=True)))
