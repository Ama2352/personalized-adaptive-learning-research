import ast
import base64
import hashlib
import json
from pathlib import Path

root=Path.cwd()
path=root/'notebooks/akt_colab_synthetic.ipynb'
notebook=json.loads(path.read_text(encoding='utf-8'))
bundle=root/'artifacts/akt/colab/akt-synthetic-20261107-v12.zip'
digest=hashlib.sha256(bundle.read_bytes()).hexdigest()
assert digest=='ddb35b8eb39906eea6ca6d1ad629d849d398ce4111ee95f3eca64ed9d369155b'
encoded=base64.b64encode(bundle.read_bytes()).decode()
cell=next(c for c in notebook['cells'] if c['id']=='akt-bootstrap')
source=''.join(cell['source'])
tree=ast.parse(source)
edits=[]
for node in tree.body:
    if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name):
        name=node.targets[0].id
        if name=='EXPECTED_BUNDLE_SHA256':replacement=f'EXPECTED_BUNDLE_SHA256 = {digest!r}\n'
        elif name=='BUNDLE_BASE64':replacement='BUNDLE_BASE64 = (\n'+''.join('    '+repr(encoded[i:i+120])+'\n' for i in range(0,len(encoded),120))+')\n'
        else:continue
        edits.append((node.lineno-1,node.end_lineno,replacement))
lines=source.splitlines(keepends=True)
assert len(edits)==2
for start,end,replacement in sorted(edits,reverse=True):lines[start:end]=[replacement]
cell['source']=''.join(lines).splitlines(keepends=True)
notebook['metadata']['kltn'].update(embedded_source_bundle=bundle.name,bundle_sha256=digest,scope='Synthetic source handoff; acceptance requires actual exported CPU/CUDA artifacts')
for c in notebook['cells']:
    if c['cell_type']=='markdown':c['source']=''.join(c['source']).replace('v11','v12').splitlines(keepends=True)
for c in notebook['cells']:
    if c['cell_type']=='code':ast.parse(''.join(c['source']))
path.write_text(json.dumps(notebook,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
mapping=json.loads((root/'artifacts/akt/colab/mcp-cell-map.json').read_text())['cells']
for local_id in ('akt-bootstrap','akt-setup'):
    source=''.join(next(c['source'] for c in notebook['cells'] if c['id']==local_id))
    request=root/'artifacts/akt/colab/requests'/('update-'+local_id+'-v12.json')
    request.write_text(json.dumps({'cellId':mapping[local_id],'content':source}),encoding='utf-8')
    assert request.stat().st_size<1024*1024
print(json.dumps({'bundle':bundle.name,'sha256':digest,'updated_cells':2}))
