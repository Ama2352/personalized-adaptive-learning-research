"""Tích hợp primitive IO sau khi mười fixture đã đạt."""
from pathlib import Path
import hashlib

root = Path(__file__).resolve().parents[4]
p = Path(__file__).resolve().parent
source = p / 'main_selection_file_primitives_candidate02.py'
tests = p / 'test_main_selection_file_primitives_candidate02.py'
assert hashlib.sha256(source.read_bytes()).hexdigest() == 'e4296d33135f17d2a75ad972baeac7718ae88847fac0a93ca1990cee999b7d6a'
assert hashlib.sha256(tests.read_bytes()).hexdigest() == '3024e47cd7f0294fbe97f40093a863b566181b7e7c124aeebfa54024152621a1'
target = root / 'src/knowledge_tracing/research_selection_io.py'
test_target = root / 'tests/shared_kt/test_research_selection_io.py'
assert not target.exists() and not test_target.exists()
target.write_bytes(source.read_bytes())
text = tests.read_text(encoding='utf-8')
start = text.index('SOURCE = Path(__file__)')
end = text.index("H = 'a' * 64", start)
text = text[:start] + 'from knowledge_tracing import research_selection_io as m\n' + text[end:]
text = text.replace('import importlib.util\n', '').replace('import sys\n', '')
test_target.write_text(text, encoding='utf-8', newline='\n')
print('Canonical IO module/test tích hợp; chưa chạy integration canonical.')
