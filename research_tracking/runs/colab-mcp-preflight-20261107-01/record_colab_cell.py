"""Đối chiếu response addcell mới và ghi local→remote ID; không gọi GPU."""
import json
from pathlib import Path
import sys
import time

root=Path.cwd()
directory=root/'artifacts/akt/private/colab-bridge/session-1990f93a9bc34123b21dd07aa93c1207'
map_path=root/'artifacts/akt/colab/mcp-cell-map.json'
state=json.loads(map_path.read_text(encoding='utf-8'))
name=sys.argv[1]
assert name not in state['cells']
deadline=time.monotonic()+10
while True:
    path=max(directory.glob('result-*.json'),key=lambda p:p.stat().st_mtime_ns)
    if path.name!=state['last_result']:break
    if time.monotonic()>deadline:raise TimeoutError('No new tool result; do not advance')
    time.sleep(.1)
result=json.loads(path.read_text(encoding='utf-8'))
assert result['is_error'] is False
cell_id=result['structured_content']['newCellId']
assert isinstance(cell_id,str) and cell_id not in state['cells'].values()
state['cells'][name]=cell_id;state['last_result']=path.name
map_path.write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8')
(root/'artifacts/akt/colab/requests'/('run-'+name+'.json')).write_text(json.dumps({'cellId':cell_id}),encoding='utf-8')
print(json.dumps({'source_cell':name,'remote_cell':cell_id,'response':'verified'}))
