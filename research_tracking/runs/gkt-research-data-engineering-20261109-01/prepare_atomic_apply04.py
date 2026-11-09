"""Giữ helper03, thêm atomic replacement cho initializer đang tồn tại."""
import hashlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
assert Path(sys.prefix).resolve() == ROOT / '.venv'
source = (PREP / 'apply_gkt_research_data03.py').read_bytes()
assert hashlib.sha256(source).hexdigest() == 'd04071c61064f5b7974ed623247f43de0eabab3751058f5e1581fc740a15ea45'
text = source.decode('utf-8').replace("OUT = PREP/'gkt-research-data-apply03'", "OUT = PREP/'gkt-research-data-apply04'")
before = """            if target.endswith('/__init__.py'):
                need(sha(path.read_bytes()) == OLD_INIT, 'Initializer changed after snapshot')
            write(path, raw, new=not target.endswith('/__init__.py'))"""
after = """            if target.endswith('/__init__.py'):
                temporary = OUT/'prepared_gkt_init.py'
                write(temporary, raw)
                need(sha(path.read_bytes()) == OLD_INIT, 'Initializer changed after snapshot')
                os.replace(temporary, path)
                need(path.read_bytes() == raw, 'Atomic initializer readback')
            else:
                write(path, raw)"""
assert text.count(before) == 1
text = text.replace(before, after)
raw = text.encode('utf-8')
compile(raw, 'apply_gkt_research_data04.py', 'exec')
with (PREP / 'apply_gkt_research_data04.py').open('xb') as stream:
    stream.write(raw)
print(hashlib.sha256(raw).hexdigest())
