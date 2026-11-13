"""Lưu mốc implementation confidence CPU, phân biệt với fit dữ liệu nghiên cứu."""
import ast
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

BUNDLE=Path(__file__).resolve().parent
ROOT=BUNDLE.parents[2]
suite=ET.parse(BUNDLE/'tests03.xml').getroot().find('testsuite')
assert suite.attrib['tests']=='8' and all(suite.attrib[key]=='0' for key in ('failures','errors','skipped'))
summary=json.loads((BUNDLE/'crossfit-summary.json').read_text())
assert summary['scope']=='SYNTHETIC_CONFIDENCE_CPU_ONLY' and len(summary['fit_ledger'])==12
paragraph='Đã cài lõi chuẩn bị đặc trưng và crossfit confidence cho Junyi, có kiểm vocabulary717. Đặc trưng chỉ dùng quá khứ trong đúng cửa sổ AKT. Fitter tái dùng solver và learner bootstrap của Method24, fit theo từng child để hỗ trợ xử lý giới hạn RAM. Kiểm CPU với solver thật xác nhận loại người học thuộc fold đánh giá khỏi dữ liệu fit và giữ confidence null khi thiếu hỗ trợ. Đây là kiểm trên dữ liệu tổng hợp. Worker train80, artifact confidence và tích hợp A2/A3 còn cần hoàn thiện trước training chính.'
current=ROOT/'research_tracking/supervisor_reports/2026-11-10/01_tien_do'
path=current/'BAO_CAO.md'
text=path.read_text(encoding='utf-8')
end=text.index('\n')
path.write_text(text[:end]+'\n\n## 13/11 — lõi confidence Junyi đã kiểm CPU\n\n'+paragraph+'\n'+text[end:],encoding='utf-8')
path=current/'BAO_CAO_NGHIEN_CUU.html'
text=path.read_text(encoding='utf-8')
anchor='<section id="junyi-comparison-admission-20261113"'
assert anchor in text
section='<section id="junyi-confidence-core-20261113"><h2>13/11 — lõi confidence Junyi đã kiểm CPU</h2><p>'+paragraph+'</p></section>\n'
path.write_text(text.replace(anchor,section+anchor,1),encoding='utf-8')
for name,link in [('docs/REPOSITORY_MAP.md','../research_tracking/runs/junyi-confidence-core-20261113-01/README.md'),
                  ('research_tracking/reports/README.md','../runs/junyi-confidence-core-20261113-01/README.md')]:
    path=ROOT/name
    text=path.read_text(encoding='utf-8')
    end=text.index('\n')
    path.write_text(text[:end]+'\n\n## 13/11 — confidence Junyi theo native window\n\n[Hồ sơ CPU]('+link+') giữ kiểm717exercise, crossfit solver thật, ledger và unsupported null trên dữ liệu tổng hợp. Worker/artifact/model A2/A3 còn chờ.\n'+text[end:],encoding='utf-8')
path=ROOT/'docs/thesis_recovery/INVESTIGATION_STATE.json'
state=json.loads(path.read_text(encoding='utf-8-sig'))
state['junyi_confidence_core_20261113']=dict(evidence=BUNDLE.relative_to(ROOT).as_posix(),
    implementation='FEATURE_ITERATOR_AND_SINGLE_CHILD_CROSSFIT',cpu_confidence_tests=8,
    synthetic_only=True,real_junyi_confidence_fitted=False,a2_a3_junyi_ready=False,
    next_vi='Worker spool train80 và fold index dùng chung, artifact loader giữ null/provenance, nối A2/A3 và kiểm source mới trước GPU.')
path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
sources=[ROOT/'src/knowledge_tracing/akt/research_junyi_confidence.py',ROOT/'tests/akt/test_junyi_confidence.py']
for source in sources:
    ast.parse(source.read_text(encoding='utf-8-sig'))
files=[*sorted(BUNDLE.glob('*')),*sources]
inventory={path.relative_to(ROOT).as_posix():dict(bytes=path.stat().st_size,
    sha256=hashlib.sha256(path.read_bytes()).hexdigest()) for path in files if path.is_file()}
(BUNDLE/'manifest.json').write_text(json.dumps(dict(status='CLOSED',files=inventory),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Đã lưu mốc confidence CPU và cập nhật báo cáo.')
