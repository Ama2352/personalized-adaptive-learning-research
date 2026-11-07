"""Tái kiểm CPU/localhost với temp dưới workspace; không ghi đè trial01."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
sources=sorted((ROOT/"src/research_demo").rglob("*.py"))+sorted((ROOT/"src/research_demo/static").glob("*"))+[ROOT/"tests/demo/test_viewer.py"]
inventory={}
for source in sources:
    relative=source.relative_to(ROOT).as_posix()
    data=source.read_bytes()
    destination=OUT/"source-before-trial02"/relative
    destination.parent.mkdir(parents=True,exist_ok=True)
    with destination.open("xb") as stream:stream.write(data)
    inventory[relative]=hashlib.sha256(data).hexdigest()
command=[sys.executable,"-m","pytest","tests/demo/test_viewer.py","-q","-p","no:cacheprovider","--basetemp="+str(OUT/"tmp02"),"--junitxml="+str(OUT/"pytest-trial02.xml")]
start=time.perf_counter()
with (OUT/"pytest-trial02.log").open("xb") as stream:
    result=subprocess.run(command,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,timeout=60)
post={source.relative_to(ROOT).as_posix():hashlib.sha256(source.read_bytes()).hexdigest() for source in sources}
assert inventory==post,"Source changed during targeted tests"
(OUT/"trial02-receipt.json").write_text(json.dumps({"command":command,"exit_code":result.returncode,"elapsed_seconds":time.perf_counter()-start,"model_or_simulator_runs":0,"source_sha256":inventory,"source_post_sha256":post},indent=2)+"\n",encoding="utf8")
print((OUT/"pytest-trial02.log").read_text(encoding="utf8"))
raise SystemExit(result.returncode)
