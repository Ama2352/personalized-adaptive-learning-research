"""Tích hợp helper đã kiểm, giữ nguyên nguồn candidate lịch sử."""
from pathlib import Path
import hashlib

root = Path(__file__).resolve().parents[4]
prep = Path(__file__).resolve().parent
source = prep / 'main_selection_population_candidate01.py'
tests = prep / 'test_main_selection_population_candidate01.py'
assert hashlib.sha256(source.read_bytes()).hexdigest() == '8709f62a4aeed14bb3bfd8581e419205a0e8695d7eb3312832c96d7b64ef1906'
assert hashlib.sha256(tests.read_bytes()).hexdigest() == 'ce9c8626193326ab2a43ebc65da81917b49f2139da3066885bf4e11005f66627'
target = root / 'src/knowledge_tracing/research_population.py'
test_target = root / 'tests/shared_kt/test_research_population.py'
assert not target.exists() and not test_target.exists()
target.write_bytes(source.read_bytes())
text = tests.read_text(encoding='utf-8')
start = text.index("PATH = Path(__file__).with_name(")
end = text.index('\n\n\ndef digest', start)
text = text[:start] + 'from knowledge_tracing import research_population as candidate' + text[end:]
for unused in ['import importlib.util\n', 'from pathlib import Path\n', 'import sys\n']:
    text = text.replace(unused, '')
test_target.write_text(text, encoding='utf-8')
print('Canonical helper và sáu tests đã tích hợp, chưa chạy kiểm canonical.')
