"""Kiểm AST wiring và import module ở đường dẫn nông, không gọi cloud."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).parent
NAMES = ('modal_junyi_engineering','modal_graph_selected','modal_a0_gpu_pilot')


def function_name(call):
    if isinstance(call.func,ast.Name):
        return call.func.id
    if isinstance(call.func,ast.Attribute):
        return call.func.attr
    return None


def ast_checks(name):
    path = ROOT/'experiments/akt'/(name+'.py')
    raw = path.read_bytes()
    tree = ast.parse(raw,filename=str(path))
    before_path = BUNDLE/(name+'_before_guard.py')
    before = ast.parse(before_path.read_bytes())
    remote_names = ('remote_epoch',) if name=='modal_junyi_engineering' else ('remote_train',) if name=='modal_a0_gpu_pilot' else ('prepare','read_billing')
    for remote in remote_names:
        previous = next(node for node in before.body if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name==remote)
        current = next(node for node in tree.body if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name==remote)
        assert ast.dump(previous)==ast.dump(current), remote+' scientific worker changed'
    # Các tham số phần cứng/hàm cloud giữ nguyên.
    for function in ('function','from_id','from_name'):
        calls = lambda source:[ast.dump(node) for node in ast.walk(source)
                               if isinstance(node,ast.Call) and function_name(node)==function]
        assert calls(before)==calls(tree), function+' cloud allocation changed'
    guards = [node for node in ast.walk(tree) if isinstance(node,ast.With)
              and any(isinstance(item.context_expr,ast.Call) and function_name(item.context_expr)=='ModalAppBudgetGuard'
                      for item in node.items)]
    assert len(guards)==1
    guard = guards[0]
    inner_runs = [node for node in ast.walk(guard) if isinstance(node,ast.With)
                  and any(isinstance(item.context_expr,ast.Call) and function_name(item.context_expr)=='run'
                          for item in node.items)]
    assert len(inner_runs)==1
    gets = [node for node in ast.walk(tree) if isinstance(node,ast.Call)
            and isinstance(node.func,ast.Attribute) and node.func.attr=='get'
            and isinstance(node.func.value,ast.Name) and node.func.value.id=='call']
    assert len(gets)==1
    timeout = next(keyword.value for keyword in gets[0].keywords if keyword.arg=='timeout')
    assert isinstance(timeout,ast.Call) and ast.unparse(timeout)=='guard.remaining()'
    assert any(node is gets[0] for node in ast.walk(inner_runs[0]))
    top_level_helper_imports = [node for node in tree.body if isinstance(node,ast.ImportFrom) and node.module=='modal_budget_guard']
    assert not top_level_helper_imports
    deadlines = [node for node in ast.walk(tree) if isinstance(node,ast.Call) and function_name(node)=='ModalRunDeadline']
    assert len(deadlines)==1
    time_limit = ast.unparse(deadlines[0].args[0])
    assert time_limit==('800 if args.main60 else 380' if name=='modal_a0_gpu_pilot' else '800')
    return dict(source_sha256=hashlib.sha256(raw).hexdigest(),
        before_sha256=hashlib.sha256(before_path.read_bytes()).hexdigest(),
        guard_outside_app_run=True,call_get_uses_remaining_deadline=True,
        helper_import_local_only=True,worker_and_cloud_configuration_unchanged=True,
        total_deadline_seconds=time_limit)


program = """
import os,sys,types
from pathlib import Path
root=Path(sys.argv[1])
for name in ('modal_a0_gpu_pilot','modal_junyi_engineering','modal_graph_selected'):
    module=types.ModuleType(name)
    module.__file__='/root/'+name+'.py'
    sys.modules[name]=module
    text=(root/'experiments/akt'/(name+'.py')).read_text(encoding='utf-8')
    exec(compile(text,module.__file__,'exec'),module.__dict__)
assert 'modal_budget_guard' not in sys.modules
assert 'torch' not in sys.modules
print('THREE_STANDALONE_IMPORTS_PASS_NO_HELPER_OR_TORCH')
"""

result = {name:ast_checks(name) for name in NAMES}
completed = subprocess.run([sys.executable,'-B','-c',program,str(ROOT)],
    timeout=20,check=True,capture_output=True,text=True)
(BUNDLE/'standalone-import.log').write_text(completed.stdout+completed.stderr,encoding='utf-8')
(BUNDLE/'controller-integration.json').write_text(json.dumps(dict(status='THREE_CONTROLLERS_STATIC_IMPORT_VERIFIED',
    controllers=result,cloud_execution_performed=False),indent=2)+'\n')
print(completed.stdout.strip())
print('AST guard nesting, timeout, scientific worker and cloud hardware calls verified')
