"""Cập nhật tiến độ sau khi nối guard và kiểm quần thể target thật."""
import ast
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

BUNDLE=Path(__file__).resolve().parent
ROOT=BUNDLE.parents[2]
suite=ET.parse(BUNDLE/'tests04.xml').getroot().find('testsuite')
assert suite.attrib['tests']=='77' and all(suite.attrib[key]=='0' for key in ('failures','errors','skipped'))
population=json.loads((BUNDLE/'selection-population.json').read_text())
assert population['status']=='PASS_INDEPENDENT_SELECTION_TARGET_POPULATION'
paragraph='Đã nối kiểm tương thích vào luồng training graph chính. Trước bước optimizer đầu tiên, producer đối chiếu đầu vào thực, cấu hình và khởi tạo backbone với tham chiếu A0. Main còn kiểm lại cache trước khi dựng model. Mỗi validation đối chiếu target population với A0 và checkpoint ghi tham chiếu để bảo vệ resume. Bộ hồi quy CPU đạt77ca. Một lượt SQL độc lập đã kiểm đủ1.600.343target selection của15.847người học,0OOV và khớp từng khóa cùng thứ tự với A0 H100. Confidence và producer A2/A3 Junyi cùng dự toán toàn ma trận vẫn đang cần hoàn thiện trước main GPU.'
current=ROOT/'research_tracking/supervisor_reports/2026-11-10/01_tien_do'
path=current/'BAO_CAO.md'
text=path.read_text(encoding='utf-8')
end=text.index('\n')
path.write_text(text[:end]+'\n\n## 13/11 — kiểm được gắn vào luồng training chính\n\n'+paragraph+'\n'+text[end:],encoding='utf-8')
path=current/'BAO_CAO_NGHIEN_CUU.html'
text=path.read_text(encoding='utf-8')
anchor='<section id="junyi-comparison-preflight-20261113"'
assert anchor in text
section='<section id="junyi-comparison-admission-20261113"><h2>13/11 — kiểm được gắn vào luồng training chính</h2><p>'+paragraph+'</p></section>\n'
path.write_text(text.replace(anchor,section+anchor,1),encoding='utf-8')
for name,link in [('docs/REPOSITORY_MAP.md','../research_tracking/runs/junyi-comparison-admission-20261113-01/README.md'),
                  ('research_tracking/reports/README.md','../runs/junyi-comparison-admission-20261113-01/README.md')]:
    path=ROOT/name
    text=path.read_text(encoding='utf-8')
    end=text.index('\n')
    path.write_text(text[:end]+'\n\n## 13/11 — guard so sánh đã nối vào producer\n\n[Hồ sơ]('+link+') có77ca CPU đạt và kiểm SQL độc lập1.600.343selection targets khớp A0. Confidence Junyi và kiểm source Linux tiếp theo còn chờ.\n'+text[end:],encoding='utf-8')
path=ROOT/'docs/thesis_recovery/INVESTIGATION_STATE.json'
state=json.loads(path.read_text(encoding='utf-8-sig'))
state['junyi_comparison_admission_20261113']=dict(evidence=BUNDLE.relative_to(ROOT).as_posix(),
    main_graph_reference_required=True,cpu_tests=77,independent_selection_targets=1600343,
    selection_population_matches_a0=True,new_source_cuda_verified=False,
    a2_a3_junyi_ready=False,paid_training_ready=False,
    next_vi='Adapter confidence Junyi theo learner-disjoint train80 và native-window history, kiểm source mới trên Linux/T4, dự toán toàn ma trận.')
path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
sources=['src/knowledge_tracing/akt/research_junyi_selection.py','src/knowledge_tracing/akt/comparison_contract.py',
    'scripts/akt/run_junyi_selected.py','scripts/akt/verify_junyi_selection_population.py',
    'tests/akt/test_junyi_selected_runner.py','tests/akt/test_junyi_comparison_admission.py','tests/akt/test_comparison_contract.py']
for name in sources:
    ast.parse((ROOT/name).read_text(encoding='utf-8-sig'))
files=[*sorted(BUNDLE.glob('*')),*[ROOT/name for name in sources]]
inventory={path.relative_to(ROOT).as_posix():dict(bytes=path.stat().st_size,
    sha256=hashlib.sha256(path.read_bytes()).hexdigest()) for path in files if path.is_file()}
(BUNDLE/'manifest.json').write_text(json.dumps(dict(status='CLOSED',files=inventory),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Đã cập nhật báo cáo và đóng gói admission.')
