"""Kiểm notebook/canary integrity, lưu inventory trước/sau copy."""
import hashlib
import json
from pathlib import Path
import runpy
import shutil
import time

started = time.monotonic()
root = Path.cwd()
prep = root / 'artifacts/akt/local-tests/thesis-evidence-notebook-20261108-01'
script = root / 'scripts/research/build_thesis_evidence_notebook.py'
notebook_path = root / 'notebooks/thesis_evidence_report.ipynb'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
helpers = runpy.run_path(str(script))
source_map_path = root / helpers['MAP_PATH']
before = {p.relative_to(root).as_posix(): sha(p) for p in (script, notebook_path, source_map_path)}
verified = helpers['load_verified_evidence'](root)
assert (verified['verified_inputs'], verified['verified_claims'], verified['verified_pointers']) == (28, 14, 104)
checks = ['28inputs_14claims_104pointers_hash_and_value_verified']
assert helpers['json_pointer']({'a/b': [{'~': 7}]}, '/a~1b/0/~0') == 7
checks.append('RFC6901_escaped_pointer')
assert '<script>' not in helpers['table'](['x'], [['<script>unsafe</script>']])
checks.append('HTML_table_escapes_values')
globals_dict = helpers['load_verified_evidence'].__globals__
saved = globals_dict['MAP_SHA256']
try:
    globals_dict['MAP_SHA256'] = '0' * 64
    try:
        helpers['load_verified_evidence'](root)
    except ValueError as error:
        assert 'source-map drift' in str(error)
    else:
        raise AssertionError('SHA drift was not rejected')
finally:
    globals_dict['MAP_SHA256'] = saved
checks.append('tampered_expected_SHA_rejected_without_editing_historical_files')
try:
    helpers['resolve_repository_file'](root, '../outside.json')
except ValueError:
    pass
else:
    raise AssertionError('outside-repository source accepted')
checks.append('outside_repository_read_rejected')
notebook = json.loads(notebook_path.read_text(encoding='utf-8'))
assert notebook['nbformat'] == 4 and notebook['nbformat_minor'] == 5
assert len(notebook['cells']) == 14 and len({c['id'] for c in notebook['cells']}) == 14
code_cells = [c for c in notebook['cells'] if c['cell_type'] == 'code']
assert [c['execution_count'] for c in code_cells] == list(range(1, 8))
assert all(c['outputs'] and all(o['output_type'] in ('display_data', 'stream') for o in c['outputs']) for c in code_cells)
checks.append('notebook_JSON_schema_subset_and_seven_executed_cells')
rerender = helpers['make_notebook'](root)
helpers['execute_report_cells'](rerender)
assert rerender == notebook
checks.append('seven_report_cells_reexecute_to_identical_outputs_without_kernel')
after = {p.relative_to(root).as_posix(): sha(p) for p in (script, notebook_path, source_map_path)}
assert before == after
checks.append('builder_notebook_and_source_map_unchanged')
elapsed = time.monotonic() - started
assert elapsed <= 30
receipt = dict(status='PASS_STDLIB_REPORT_VALIDATION_NOT_JUPYTER_QA', checks=checks,
    verified_inputs=28, verified_claims=14, verified_pointers=104, executed_report_cells=7,
    elapsed_seconds=elapsed, cap_seconds=30, before_sha256=before, after_sha256=after,
    model_training_or_simulator_runs=0, new_research_observations=0,
    global_or_venv_installs=0, network_or_cloud_spend=False,
    limitation='No Jupyter-kernel/nbformat library or visual-render QA; embedded outputs computed by real stdlib cell execution.')
(prep / 'validation.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
target = root / 'research_tracking/runs/thesis-evidence-notebook-20261108-01'
inputs = [(notebook_path, 'thesis_evidence_report.ipynb'), (script, 'build_thesis_evidence_notebook.py'),
          (prep / 'validation.json', 'validation.json'), (prep / 'build01.log', 'build01.log'),
          (Path(__file__), 'verify_and_archive.py')]
inventory = [{'source': p.relative_to(root).as_posix(), 'destination': name, 'sha256': sha(p)} for p, name in inputs]
(prep / 'copy_inventory_before.json').write_text(json.dumps(inventory, indent=2) + '\n', encoding='utf-8')
target.mkdir(exist_ok=False)
for (path, name), row in zip(inputs, inventory):
    assert sha(path) == row['sha256']
    shutil.copyfile(path, target / name)
    assert sha(target / name) == sha(path) == row['sha256']
(target / 'copy_inventory.json').write_text(json.dumps(inventory, indent=2) + '\n', encoding='utf-8')
(target / 'README.md').write_text('''# Notebook bằng chứng KLTN — snapshot08/11

Notebook báo cáo đã có outputs thực:7code cells/14cells, đọc28inputs kiểm14claims và104JSONPointers của source map C14. Chạy lại các cell bằng .venv/stdlib cho outputs giống hệt; tám kiểm integrity/schema-subset đạt. Không train/simulator rerun, thêm quan sát, mở Holdout, network hoặc cài thư viện.

Đây là report snapshot/pilot diagnostics, không kết quả cuối của RQ1–RQ3. Có bảng RQ1, first-break explanation, retention identity, factorial và Junyi order-only cùng source/limits. Sơ đồ nguồn dùng chuỗi S→M/R→C/B/keys→A→Pserved→interact/update, không causal funnel từ Pserved. Các tables là output từ artifact có SHA, không gõ tay số liệu.

Notebook nguồn ở notebooks/thesis_evidence_report.ipynb. Outputs được tạo bằng actual local Python cell execution; **chưa QA bằng Jupyter kernel hoặc kiểm thị giác trên viewer**, không gọi đây là nbformat-package validation. Để đọc outputs không cần install; để RunAll bằng notebook kernel cần IPython trong môi trường đã chọn. Builder không cài packages. Plot khoa học/ảnh xuất bản chưa có trong gói này.

Snapshot source map SHAfbfa712e1eaf04f05fee5a33c577393478ba7f5a766af2a836d4598a2ed73bbc. Nếu đổi inputs/builder cần review/rebuild phiên bản mới; không sửa bundle đã đóng. File validation lưu source hashes, các canary và giới hạn; inventory trước/sau copy khớp.
''', encoding='utf-8')
manifest = dict(schema_version=1, run_id=target.name, inputs_sha256=before,
                outputs_sha256={p.name: sha(p) for p in sorted(target.iterdir())})
(target / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(dict(status=receipt['status'], checks=len(checks), executed_cells=7,
    outputs=len(manifest['outputs_sha256']), manifest_sha256=sha(target / 'manifest.json'), elapsed_seconds=elapsed)))
