"""Lưu source trước chạy và targeted logs; chỉ CPU, không model/dataset."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
sources = sorted((ROOT / "src/research_demo").rglob("*.py")) + sorted((ROOT / "src/research_demo/static").glob("*")) + [ROOT/"tests/demo/test_viewer.py"]
inventory = {}
for source in sources:
    relative = source.relative_to(ROOT).as_posix()
    data = source.read_bytes()
    destination = OUT / "source-before-trial01" / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb") as stream:
        stream.write(data)
    inventory[relative] = hashlib.sha256(data).hexdigest()
(OUT/"source-before-trial01.json").write_text(json.dumps(inventory,indent=2)+"\n",encoding="utf8")
command = [sys.executable,"-m","pytest","tests/demo/test_viewer.py","-q","--junitxml="+str(OUT/"pytest-trial01.xml")]
start=time.perf_counter()
with (OUT/"pytest-trial01.log").open("xb") as stream:
    result=subprocess.run(command,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,timeout=60)
(OUT/"trial01-receipt.json").write_text(json.dumps({"command":command,"exit_code":result.returncode,"elapsed_seconds":time.perf_counter()-start,"model_or_simulator_runs":0,"source_sha256":inventory},indent=2)+"\n",encoding="utf8")
print((OUT/"pytest-trial01.log").read_text(encoding="utf8"))
raise SystemExit(result.returncode)
