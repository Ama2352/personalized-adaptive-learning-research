"""Kiểm output remote qua MCP; không chấp nhận tool success thay cell success."""
import hashlib
import json
from pathlib import Path
import sys
import time

root=Path.cwd();phase=sys.argv[1];label=sys.argv[2] if len(sys.argv)>2 else phase
markers={'connection':'CONNECTED_GPU','bootstrap':'SOURCE_READY','setup':'SETUP_READY',
         'cpu':'CPU portability PASS','lifecycle':'passed_synthetic',
         'recovery':'passed_synthetic_recovery','export':'RESULT_ZIP:'}
directory=root/'artifacts/akt/private/colab-bridge/session-1990f93a9bc34123b21dd07aa93c1207'
last=max(directory.glob('result-*.json'),key=lambda p:p.stat().st_mtime_ns)
value=json.loads(last.read_text(encoding='utf-8'));assert not value['is_error']
outputs=value['structured_content']['outputs']
assert outputs and not any(o.get('output_type')=='error' for o in outputs),outputs
raw=''.join(''.join(o.get('text',[])) for o in outputs if o.get('output_type')=='stream')
try:text=json.loads('"'+raw+'"')
except json.JSONDecodeError:text=raw
assert markers[phase] in text,(phase,text[-2500:])
target=root/'artifacts/akt/colab'/('mcp-stage-'+label+'.json')
with target.open('x',encoding='utf-8') as stream:
 json.dump({'status':'PASS_CELL_OUTPUT','phase':phase,'response_file':str(last.relative_to(root)),
    'response_sha256':hashlib.sha256(last.read_bytes()).hexdigest(),'transcript':text,
    'scope':'Actual MCP cell output; model/data acceptance also requires exported artifacts'},stream,ensure_ascii=False,indent=2)
print(json.dumps({'phase':phase,'status':'PASS_CELL_OUTPUT','transcript':text[-2500:]},ensure_ascii=False))
