import ast
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
from unittest.mock import patch
import importlib.metadata
import importlib.util

root=Path.cwd()
n=json.loads((root/'notebooks/akt_colab_synthetic.ipynb').read_text(encoding='utf-8'))
s=''.join(next(c['source'] for c in n['cells'] if c['id']=='akt-setup'))
tree=ast.parse(s)
names=('packages','required_versions','probe')
assignments=[x for x in ast.walk(tree) if isinstance(x,ast.Assign) and isinstance(x.targets[0],ast.Name) and x.targets[0].id in names]
assert len(assignments)==3
ns={}
exec(compile(ast.Module(body=assignments,type_ignores=[]),'setup-dependency-probe','exec'),ns)
records=[]
for version,missing_modules,expected in [('1.3.2',set(),['duckdb==1.5.6']),('1.5.6',set(),[]),('1.5.6',{'psutil'},['psutil']),('1.3.2',{'networkx'},['duckdb==1.5.6','networkx'])]:
    out=io.StringIO()
    with patch.object(importlib.util,'find_spec',side_effect=lambda m:None if m in missing_modules else object()),patch.object(importlib.metadata,'version',return_value=version),redirect_stdout(out):
        exec(compile(ns['probe'],'dependency-probe','exec'),{})
    actual=json.loads(out.getvalue())
    assert actual==expected,(actual,expected)
    records.append({'duckdb':version,'missing_modules':sorted(missing_modules),'requested_install':actual,'status':'PASS'})
assert "setup_command('venv-target'" in s and s.index("setup_command('venv-target'")<s.index("setup_command('packages'")
assert "[AKT_PY,'-m','pip','install','--only-binary=:all:','--report'" in s
report={'status':'PASS','cases':records,'venv_before_install_guard':True,'wheel_only_and_install_report':True,'scope':'Local mocked dependency probe; remote install separately verified'}
path=root/'artifacts/akt/local-tests/colab-dependency-pin-v12-verification.json'
with path.open('x',encoding='utf-8') as f:json.dump(report,f,indent=2)
print(json.dumps(report))
