"""Đổi workspace không bị entrypoint refit ghi đè profile đã chọn."""
import ast
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.mark.parametrize('filename', ['modal_graph_selected.py', 'modal_junyi_refit.py'])
@pytest.mark.parametrize('explicit', [False, True])
def test_modal_environment_preserves_explicit_workspace(filename, explicit):
    root = Path(__file__).resolve().parents[2]
    tree = ast.parse((root / 'experiments/akt' / filename).read_text(encoding='utf-8'))
    statements = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
            continue
        call = node.value
        if (isinstance(call.func, ast.Attribute)
                and ast.unparse(call.func.value) == 'os.environ'
                and call.args and isinstance(call.args[0], ast.Constant)
                and call.args[0].value in ('MODAL_CONFIG_PATH', 'MODAL_PROFILE')):
            assert call.func.attr == 'setdefault'
            statements.append(node)
    assert len(statements) == 2
    values = {'MODAL_CONFIG_PATH': 'D:/private/new.toml', 'MODAL_PROFILE': 'kltn2016'} if explicit else {}
    expected = dict(values)
    program = ast.fix_missing_locations(ast.Module(body=statements, type_ignores=[]))
    exec(compile(program, filename, 'exec'), {'os': SimpleNamespace(environ=values), 'ROOT': root})
    if explicit:
        assert values == expected
    else:
        assert values == {'MODAL_CONFIG_PATH': str(root / 'artifacts/akt/private/modal.toml'), 'MODAL_PROFILE': 'kltn'}


@pytest.mark.parametrize('custom', [False, True])
def test_staged_entry_uses_requested_budget_file(tmp_path, custom):
    import sys
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / 'experiments/akt'))
    from junyi_staged_io import owned_input
    tree = ast.parse((root / 'experiments/akt/modal_junyi_staged.py').read_text(encoding='utf-8'))
    statements = [node for node in ast.walk(tree) if isinstance(node, ast.Assign)
                  and any(isinstance(target, ast.Name) and target.id == 'ledger_path' for target in node.targets)]
    assert len(statements) == 1
    selected = 'research_tracking/COMPUTE_BUDGET_WORKSPACE2016.json'
    request = {'project_budget_file': selected} if custom else {}
    namespace = {'ROOT': tmp_path, 'request': request, 'owned_input': owned_input}
    program = ast.fix_missing_locations(ast.Module(body=statements, type_ignores=[]))
    exec(compile(program, 'modal_junyi_staged.py', 'exec'), namespace)
    assert namespace['ledger_path'] == tmp_path / (selected if custom else 'research_tracking/COMPUTE_BUDGET.json')
