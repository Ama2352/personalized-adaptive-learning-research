"""Dựng notebook báo cáo từ bằng chứng đã đóng; không train hoặc đọc data gốc.

Chạy cell bằng Python stdlib để lưu outputs; đây không là Jupyter-kernel QA.
Notebook mở được để đọc outputs, hoặc chạy lại trong kernel có IPython.
"""
import argparse
from contextlib import redirect_stdout
import hashlib
from html import escape
import io
import json
from pathlib import Path


MAP_PATH = 'research_tracking/reports/THESIS_RQ12_DIAGNOSTIC_RESULTS_DRAFT_20261108.sources.json'
MAP_SHA256 = 'fbfa712e1eaf04f05fee5a33c577393478ba7f5a766af2a836d4598a2ed73bbc'
SCRIPT_PATH = 'scripts/research/build_thesis_evidence_notebook.py'
V1_NOTEBOOK_SHA256 = 'de3ad54b658ea2e48e95cc1d6637dae48503f2c9d645fb9fc2c4338d116d6089'
V1_MANIFEST_SHA256 = '2100a70da6b8da2547bfeba958187b478a53f5e195e8987b1cdb1f5109eee410'


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verified_bytes(path, expected_sha256, *, expected_bytes=None, error='evidence SHA/size mismatch'):
    payload = path.read_bytes()
    if (hashlib.sha256(payload).hexdigest() != expected_sha256
            or expected_bytes is not None and len(payload) != expected_bytes):
        raise ValueError(error + ': ' + str(path))
    return payload


def resolve_repository_file(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError('missing or outside-repository evidence: ' + relative)
    return path


def json_pointer(value, pointer):
    if pointer == '':
        return value
    if not isinstance(pointer, str) or not pointer.startswith('/'):
        raise ValueError('invalid JSON pointer')
    for part in pointer[1:].split('/'):
        part = part.replace('~1', '/').replace('~0', '~')
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


def load_verified_evidence(root):
    root = Path(root).resolve()
    map_path = resolve_repository_file(root, MAP_PATH)
    source_map = json.loads(verified_bytes(map_path, MAP_SHA256,
        error='source-map drift; review and version report inputs before rebuilding'))
    report_path = resolve_repository_file(root, source_map['document'])
    verified_bytes(report_path, source_map['document_sha256'], error='draft report SHA mismatch')
    inventory = {row['path']: row for row in source_map['input_inventory']}
    cache = {}
    for name, row in inventory.items():
        path = resolve_repository_file(root, name)
        payload = verified_bytes(path, row['sha256'], expected_bytes=row['bytes'])
        if path.suffix == '.json':
            cache[name] = json.loads(payload)
    pointers = 0
    for claim in source_map['claims']:
        for item in claim['evidence']:
            if (item['path'] not in inventory or item['sha256'] != inventory[item['path']]['sha256']
                    or json_pointer(cache[item['path']], item['json_pointer']) != item['value']):
                raise ValueError('claim/pointer mismatch: ' + claim['id'])
            pointers += 1
    for name, row in inventory.items():
        if 'manifest_path' in row:
            manifest = cache[row['manifest_path']]
            if (inventory[row['manifest_path']]['sha256'] != row['manifest_sha256']
                    or json_pointer(manifest, row['manifest_pointer']) != row['sha256']):
                raise ValueError('manifest closure mismatch: ' + name)
    return dict(source_map=source_map, cache=cache, verified_inputs=len(inventory),
                verified_pointers=pointers, verified_claims=len(source_map['claims']))


def table(headers, rows):
    def cell(value):
        if isinstance(value, float):
            value = format(value, '.8g')
        elif isinstance(value, (dict, list, tuple)):
            value = json.dumps(value, ensure_ascii=False)
        return escape(str(value))
    return '<table><thead><tr>' + ''.join('<th>' + cell(h) + '</th>' for h in headers) + '</tr></thead><tbody>' + ''.join(
        '<tr>' + ''.join('<td>' + cell(value) + '</td>' for value in row) + '</tr>' for row in rows) + '</tbody></table>'


def markdown(text):
    return dict(cell_type='markdown', metadata={}, source=text.splitlines(keepends=True))


def code(text):
    return dict(cell_type='code', execution_count=None, metadata={}, outputs=[], source=text.splitlines(keepends=True))


def make_notebook(root):
    script_sha = sha256(root / SCRIPT_PATH)
    cells = [markdown('''# Bằng chứng KLTN: báo cáo chẩn đoán RQ1–RQ2

Snapshot08/11/2026. **Đây là pilot/chẩn đoán đã lưu, không kết quả cuối của ba RQ.**
Notebook chỉ đọc các artifact đóng gói, kiểm hash và dựng bảng/sơ đồ. Không train,
chạy simulator, truy vấn Junyi/Holdout hoặc kết nối cloud.

Outputs được tính thật bằng `.venv` qua bộ dựng stdlib; chưa kiểm bằng Jupyter
kernel. Không cần cài thư viện để mở đọc outputs. Khi chạy lại trong notebook,
kernel cần IPython; không cài thư viện global. Số events/tests không là số mẫu độc lập.
'''), code(f'''from pathlib import Path
import hashlib
import json

ROOT = next((p for p in (Path.cwd(), *Path.cwd().parents)
             if (p / {MAP_PATH!r}).is_file()), None)
if ROOT is None:
    raise RuntimeError("Mở notebook bên trong repository KLTN")
builder = ROOT / {SCRIPT_PATH!r}
builder_payload = builder.read_bytes()
if hashlib.sha256(builder_payload).hexdigest() != {script_sha!r}:
    raise RuntimeError("Builder đã thay đổi; cần regenerate notebook theo phiên bản mới")
helpers = {{'__name__': 'kltn_verified_report_builder', '__file__': str(builder)}}
exec(compile(builder_payload, str(builder), 'exec'), helpers)
verified = helpers['load_verified_evidence'](ROOT)
source_map, cache = verified['source_map'], verified['cache']
table = helpers['table']
def show_html(text):
    capture = globals().get('_REPORT_HTML_CAPTURE')
    if capture is not None:
        capture(text)
    else:
        from IPython.display import HTML, display
        display(HTML(text))
print(json.dumps({{k:v for k,v in verified.items() if k not in ('source_map','cache')}}, ensure_ascii=False))
'''), markdown('''## 1. Sơ đồ đọc kết quả, không phải một funnel nhân quả

Sơ đồ dưới mô tả thứ tự native Paper2 được chẩn đoán. P của bài đã chọn được
tính sau selection; không đặt Pserved ở đầu một chuỗi nhân quả dẫn đến selection.
P của current query trong fixed-stream cũng không phải toàn vector trạng thái.
'''), code('''stages = ["Trạng thái/score concept S", "Mastery M + ready R",
          "Candidates C / balanced B / keys", "Chọn concept và item A",
          "Dự đoán Pserved", "Interact rồi update"]
show_html(table(["Bước", "Thứ tự native Paper2"], [(i+1, stage) for i,stage in enumerate(stages)]))
print("S → M/R → C/B/keys → A → Pserved → interact/update")
print("Đây là sơ đồ nguồn; chưa chứng minh causal mediation hoặc graph edge-only effect.")
'''), markdown('''## 2. RQ1: thay đổi số có truyền thành thay đổi quyết định?

C01–C03. Mỗi comparison có1.080 paired pre-update snapshots, từ3 seed blocks ×
3 profiles ×120steps. Events và profiles cùng seed có thể phụ thuộc nhau. M là
event có ít nhất một concept đổi classification; A là **concept preview**, không
served action. Các cột là số đếm song song, không funnel với mẫu số giảm dần.
'''), code('''transitions = cache['research_tracking/runs/cpu-rq1-transitions-20261108-01/analysis.json']
pooled = [g for g in transitions['fixed_stream']['groups'] if g['scope'] == 'pooled']
fields = ['event_pairs','changed_probability_events','changed_mastery_events_any_concept',
          'changed_ready_events','changed_action_preview_events']
show_html(table(['Condition','Paired events','P đổi','M đổi','R đổi','A preview đổi'],
                [[g['candidate']] + [g[k] for k in fields] for g in pooled]))
full = next(g for g in pooled if g['candidate'] == 'graph_package')
selected_conditions = [r for r in full['conditional_tables']
                       if r['first'] == 'p_changed' and r['first_changed']
                       and r['second'] == 'a_changed' and not r['second_changed']]
show_html(table(['Điều kiện','Số đếm','Mẫu số','Tỷ lệ mô tả'],
                [('P đổi nhưng concept preview giữ', r['count'], r['conditional_denominator'],
                  r['conditional_fraction']) for r in selected_conditions]))
print("Package graph có thay đổi ngoài cạnh; chưa cô lập causal contribution của prerequisite edges.")
'''), markdown('''## 3. RQ1: giải thích first-break trong closed loop

C14 là reconstruction từ source hiện có, không phục hồi nguyên runner lịch sử.
Chỉ phân tích tại common observed prefix trước phân kỳ; sau đó không paired ΔP/loss
giữa hai histories khác nhau. Các nhóm dưới là giải thích key chọn **CID**, không
toàn bộ lựa chọn item hoặc chứng minh learning benefit. Không thêm independent N.
'''), code('''ranking = [row for row in source_map['derived_arithmetic'] if row['claim'] == 'C14']
show_html(table(['Condition','Cùng M/R/C/B, khác score chọn CID','Membership khác',
                'Không tuple first-break','Comparison count'],
               [(r['candidate'], r['counts']['same_membership_score_key'],
                 r['counts']['membership_diff'], r['counts']['no_tuple_break'], r['denominator']) for r in ranking]))
'''), markdown('''## 4. RQ2 — Trap1: retention có cung cấp thông tin mới?

C08. Hệ số dưới chỉ đúng cho no-practice sau T, homogeneous decay và nonnegative
gain trong fixture đã kiểm. Final state vẫn phụ thuộc lịch luyện trước đó. Không
suy mọi retention model đều không phân biệt policy.
'''), code('''retention = cache['research_tracking/runs/cpu-rq12-20261107-03/retention.json']
show_html(table(['Thông số/kiểm tra','Giá trị'], [(k,retention[k]) for k in
               ['true_forget_rate','retention_days','scaling_factor','absolute_error']]))
print("Trong điều kiện đã nêu: retained_gain14 = scaling_factor × final_net_gain.")
'''), markdown('''## 5. RQ2 — Trap2 và Trap3: điều kiện và confounding

Factorial:10 seed blocks/profile; contrast là tương tác điều kiện simulator,
chưa là causal ability-only DiD. Junyi: phân tích order-only trên inner-train,
không dùng correctness hoặc Holdout. Predictive/logged-order association không
chứng minh lợi ích giảng dạy của graph.
'''), code('''conditions = cache['research_tracking/runs/rq2-conditions-evidence-20261108-01/conditions.json']
show_html(table(['Profile','Seed blocks','Exposure fraction','Mean interaction','Signs'],
               [(r['profile'],r['seed_blocks'],r['pooled_mechanism_exposure_fraction'],
                 r['mean_lambda_edge_interaction'],r['interaction_signs'])
                for r in conditions['factorial']['profiles']]))
junyi_claim = next(c for c in source_map['claims'] if c['id'] == 'C11')
show_html(table(['Nguồn order-only','Giá trị','JSON pointer'],
               [(Path(r['path']).name,r['value'],r['json_pointer']) for r in junyi_claim['evidence'][:5]]))
for limit in conditions['limits_vi']:
    print("Giới hạn:", limit)
'''), markdown('''## 6. Phát biểu nào được phép đưa vào báo cáo?

- Có thể: chẩn đoán cơ chế, số đếm/đơn vị rõ ràng, conditional retention identity,
  nhiễu practice order và giới hạn đối chứng.
- Chưa thể: graph cải thiện học tập nhân quả, CG-AKT vượt baseline, hoặc RQ hoàn tất.
- Các PASS phần mềm đặt ở phụ lục tái lập; không dùng số tests làm hiệu quả mô hình.
- Chưa có original Paper1 revision; phân biệt current-source diagnosis và reproduction.

Mỗi C-ID bên dưới trỏ tới source map có đường dẫn, SHA và JSON Pointer/giá trị.
'''), code('''show_html(table(['Claim ID','Phát biểu/nhóm chứng cứ','Số pointers'],
               [(c['id'],c['claim_vi'],len(c['evidence'])) for c in source_map['claims']]))
print("Source map:", ROOT / helpers['MAP_PATH'])
print("Source map SHA:", helpers['MAP_SHA256'])
print("Bản thảo:", ROOT / source_map['document'])
''')]
    return dict(nbformat=4, nbformat_minor=5, cells=cells,
                metadata=dict(kernelspec=dict(display_name='Python (.venv KLTN)', language='python', name='python3'),
                              language_info=dict(name='python', version='3.11+'),
                              kltn=dict(scope='stored_diagnostic_report_not_final_RQ', source_map_sha256=MAP_SHA256,
                                        execution_mode='local_stdlib_cell_execution_not_jupyter_kernel')))


def execute_report_cells(notebook):
    namespace = {}
    for index, cell in enumerate(notebook['cells']):
        cell['id'] = 'kltn-report-%02d' % index
        if cell['cell_type'] != 'code':
            continue
        outputs, stdout = [], io.StringIO()
        namespace['_REPORT_HTML_CAPTURE'] = lambda text: outputs.append(dict(
            output_type='display_data', data={'text/html': text}, metadata={}))
        with redirect_stdout(stdout):
            exec(compile(''.join(cell['source']), '<KLTN report cell %d>' % index, 'exec'), namespace)
        if stdout.getvalue():
            outputs.append(dict(output_type='stream', name='stdout', text=stdout.getvalue()))
        cell['execution_count'] = sum(c['cell_type'] == 'code' for c in notebook['cells'][:index+1])
        cell['outputs'] = outputs
    return namespace['verified']


def verify_v1_replacement(root, target, expected_sha256):
    if (expected_sha256 != V1_NOTEBOOK_SHA256
            or target != root / 'notebooks/thesis_evidence_report.ipynb' or target.is_symlink()):
        raise ValueError('replacement requires exact reviewed V1 SHA and canonical generated notebook')
    before = verified_bytes(target, expected_sha256, error='generated notebook replacement SHA mismatch')
    bundle = root / 'research_tracking/runs/thesis-evidence-notebook-20261108-01'
    manifest_path = bundle / 'manifest.json'
    manifest = json.loads(verified_bytes(manifest_path, V1_MANIFEST_SHA256, error='V1 archive manifest mismatch'))
    outputs = manifest['outputs_sha256']
    archived = {}
    for name, digest in outputs.items():
        path = bundle / name
        if Path(name).name != name or path.is_symlink():
            raise ValueError('unsafe V1 archive member')
        payload = verified_bytes(path, digest, error='V1 archive output mismatch')
        archived[name] = dict(sha256=digest, bytes=len(payload))
    if (len(archived) != 7 or archived['thesis_evidence_report.ipynb']['sha256'] != expected_sha256
            or archived['thesis_evidence_report.ipynb']['bytes'] != len(before)):
        raise ValueError('V1 archived notebook replacement binding mismatch')
    return before, dict(generated_path=target.relative_to(root).as_posix(), sha256=expected_sha256,
                        bytes=len(before), verified_v1_manifest_sha256=V1_MANIFEST_SHA256,
                        verified_v1_outputs=archived)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='notebooks/thesis_evidence_report.ipynb')
    parser.add_argument('--replace-generated-sha256', help='Chỉ thay working notebook V1 đúng SHA đã review; giữ archive V1')
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    target = (root / args.output).resolve()
    if target.parent != root / 'notebooks' or target.suffix != '.ipynb':
        raise ValueError('report notebook output must be directly under notebooks/')
    replacement = None
    if args.replace_generated_sha256 is not None:
        if (root / args.output).is_symlink():
            raise ValueError('generated notebook replacement cannot follow a symlink')
        replacement = verify_v1_replacement(root, target, args.replace_generated_sha256)
    notebook = make_notebook(root)
    verified = execute_report_cells(notebook)
    payload = (json.dumps(notebook, ensure_ascii=False, indent=1, allow_nan=False) + '\n').encode('utf-8')
    if replacement is None:
        with target.open('xb') as stream:
            stream.write(payload)
    else:
        before, inventory = replacement
        prep = root / 'artifacts/akt/local-tests/thesis-evidence-notebook-20261108-02'
        prep.mkdir(parents=True, exist_ok=True)
        with (prep / 'notebook-before.ipynb').open('xb') as stream:
            stream.write(before)
        inventory['backup_path'] = (prep / 'notebook-before.ipynb').relative_to(root).as_posix()
        inventory['backup_sha256'] = sha256(prep / 'notebook-before.ipynb')
        if inventory['backup_sha256'] != inventory['sha256']:
            raise ValueError('notebook backup SHA mismatch')
        with (prep / 'replacement-before.json').open('x', encoding='utf-8') as stream:
            json.dump(inventory, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
        with target.open('r+b') as stream:
            if stream.read() != before:
                raise ValueError('generated notebook changed after replacement approval')
            stream.seek(0)
            stream.write(payload)
            stream.truncate()
    if sha256(target) != hashlib.sha256(payload).hexdigest():
        raise ValueError('generated notebook publication SHA mismatch')
    print(json.dumps(dict(output=target.relative_to(root).as_posix(), sha256=sha256(target),
                          inputs=verified['verified_inputs'], claims=verified['verified_claims'],
                          pointers=verified['verified_pointers'], research_reruns=0)))


if __name__ == '__main__':
    main()
