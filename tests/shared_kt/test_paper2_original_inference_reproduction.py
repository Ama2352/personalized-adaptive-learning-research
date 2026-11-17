"""Kiểm CLI mới và AST recipe nguồn, không chạy simulator hoặc bootstrap trong test."""
import ast
import importlib.util
from pathlib import Path
import sys

import pytest

SPEC=importlib.util.spec_from_file_location('paper2_original_reproduction',Path(__file__).resolve().parents[2]/
    'research_tracking/runs/paper2-statistical-reproduction-20261117-02/reproduce_original_inference.py')
module=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def test_exact_source_recipe_seed_functions_and_metric_order():
    recipe=module.original_recipe()
    assert recipe['global_seed']==20260721 and recipe['samples']==3000
    assert recipe['personas']==('PG','PY','PYH')
    assert tuple(recipe['directions']['replay_directions'])==('auc','log_loss','brier','ece','p_true_mae')
    assert tuple(node.name for node in recipe['definitions'])==module.FUNCTIONS
    paired=next(node for node in recipe['definitions'] if node.name=='paired_tests')
    wilcoxon=[node for node in ast.walk(paired) if isinstance(node,ast.Call)
              and isinstance(node.func,ast.Name) and node.func.id=='wilcoxon']
    assert len(wilcoxon)==1
    assert {kw.arg:ast.literal_eval(kw.value) for kw in wilcoxon[0].keywords}==dict(zero_method='wilcox',alternative='two-sided')


def test_normal_cli_uses_fresh_output_without_editing_source(tmp_path,monkeypatch):
    monkeypatch.setattr(module,'ROOT',tmp_path)
    output=tmp_path/'research_tracking/runs/paper2-statistical-reproduction-20261117-02/attempt-test'
    called=[]
    monkeypatch.setattr(module,'guarded',lambda path:called.append(path))
    monkeypatch.setattr(sys,'argv',['reproduce','--output',str(output)])
    module.main()
    assert output.is_dir() and called==[output]
    with pytest.raises(FileExistsError):module.main()


def test_cli_rejects_foreign_output_before_execution(tmp_path,monkeypatch):
    monkeypatch.setattr(module,'ROOT',tmp_path)
    output=tmp_path/'foreign'
    monkeypatch.setattr(sys,'argv',['reproduce','--output',str(output)])
    with pytest.raises(SystemExit):module.main()
    assert not output.exists()
