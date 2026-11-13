"""Lưu trạng thái đã kiểm CPU, còn chờ số đo T4 và kiểm A0 thật."""
import ast
import hashlib
import json
import re
from pathlib import Path
import xml.etree.ElementTree as ET

BUNDLE=Path(__file__).resolve().parent
ROOT=BUNDLE.parents[2]
suite=ET.parse(BUNDLE/'tests04.xml').getroot().find('testsuite')
assert suite.attrib['tests']=='126' and all(suite.attrib[key]=='0' for key in ('failures','errors','skipped'))
paragraph='Đã nối validation và xuất dự báo theo batch tối đa128cửa sổ, giữ ranh giới lịch sử từng learner và các target/OOV. Bộ kiểm local đạt126ca, gồm native AKT/A1 trên CPU và kiểm trạng thái mô hình, thứ tự dữ liệu, grant và resume. Mode chạy mới có định danh riêng để tránh trộn với validation từng cửa sổ của A0 trước đây. Chưa có số đo tăng tốc T4 hoặc kết quả kiểm lại toàn selection bằng checkpoint A0, nên chưa nghiệm thu tối ưu cho training chính.'


def update_markdown(path,heading,body):
    text=path.read_text(encoding='utf-8')
    pattern=r'\n## '+re.escape(heading)+r'\n.*?(?=\n## |\Z)'
    section='\n## '+heading+'\n\n'+body+'\n'
    if re.search(pattern,text,re.S):
        text=re.sub(pattern,lambda _:section,text,count=1,flags=re.S)
    else:
        end=text.index('\n')
        text=text[:end]+'\n'+section+text[end:]
    path.write_text(text,encoding='utf-8')
current=ROOT/'research_tracking/supervisor_reports/2026-11-10/01_tien_do'
path=current/'BAO_CAO.md'
update_markdown(path,'13/11 — chuẩn bị tối ưu validation',paragraph)
path=current/'BAO_CAO_NGHIEN_CUU.html'
text=path.read_text(encoding='utf-8');anchor='<section id="junyi-confidence-core-20261113"'
assert anchor in text
section='<section id="junyi-validation-batch-20261113"><h2>13/11 — chuẩn bị tối ưu validation</h2><p>'+paragraph+'</p></section>\n'
pattern=r'<section id="junyi-validation-batch-20261113">.*?</section>\n?'
if re.search(pattern,text,re.S):
    text=re.sub(pattern,lambda _:section,text,count=1,flags=re.S)
else:
    text=text.replace(anchor,section+anchor,1)
path.write_text(text,encoding='utf-8')
for name,link in [('docs/REPOSITORY_MAP.md','../research_tracking/runs/junyi-validation-batch-20261113-01/README.md'),
                  ('research_tracking/reports/README.md','../runs/junyi-validation-batch-20261113-01/README.md'),
                  ('notebooks/README.md','../research_tracking/runs/junyi-validation-batch-20261113-01/README.md')]:
    update_markdown(ROOT/name,'13/11 — validation theo batch',
        '[Hồ sơ]('+link+') có126ca CPU đạt, probe và notebook T4 đã chuẩn bị. Chưa có GPU speedup hoặc A0 full-selection parity.')
state_path=ROOT/'docs/thesis_recovery/INVESTIGATION_STATE.json'
state=json.loads(state_path.read_text(encoding='utf-8-sig'))
state['junyi_validation_batch_20261113']=dict(evidence=BUNDLE.relative_to(ROOT).as_posix(),
    cpu_tests=126,mode='batched_windows_v1_batch128',t4_verified=False,
    a0_full_selection_parity=False,main_training_adopted=False,modal_spent_this_batch=0,
    colab_client_session_id=75295,colab_client_ttl_seconds=3600,
    next_vi='Chờ MCP/T4, đo synthetic validation probe, tải artifact về D, kiểm lại checkpoint A0 trước nhận vào main comparison.')
state_path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
sources=['src/knowledge_tracing/akt/prediction_batch.py','src/knowledge_tracing/akt/research_junyi_selection.py',
    'scripts/akt/run_junyi_selected.py','scripts/akt/synthetic_validation_batch_probe.py',
    'tests/akt/test_prediction_batch.py','tests/akt/test_junyi_validation_batch.py','tests/akt/test_junyi_selected_runner.py']
for name in sources:
    ast.parse((ROOT/name).read_text(encoding='utf-8-sig'))
notebook=json.loads((ROOT/'notebooks/akt_colab_validation_batch.ipynb').read_text(encoding='utf-8'))
for index,cell in enumerate(notebook['cells']):
    if cell['cell_type']=='code':
        compile(''.join(cell['source']),f'cell-{index}','exec')
files=[*sorted(BUNDLE.glob('*')),*[ROOT/name for name in sources],ROOT/'notebooks/akt_colab_validation_batch.ipynb']
inventory={path.relative_to(ROOT).as_posix():dict(bytes=path.stat().st_size,
    sha256=hashlib.sha256(path.read_bytes()).hexdigest()) for path in files
    if path.is_file() and path.name!='manifest-cpu.json'}
(BUNDLE/'manifest-cpu.json').write_text(json.dumps(dict(status='CPU_SNAPSHOT_GPU_PENDING',files=inventory),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Đã lưu snapshot CPU và trạng thái chờ T4.')
