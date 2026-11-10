"""Đọc backlog và hash ba PDF người dùng chỉ định, không đọc dataset/Test."""
from pathlib import Path
import hashlib
import json

root = Path(__file__).resolve().parents[4]
prep = Path(__file__).resolve().parent
out = prep / 'research-readiness-reconciliation01'
out.mkdir(exist_ok=False)
tasks = json.loads((root / 'docs/thesis_recovery/TASKS.json').read_bytes())
print('tasks', len(tasks['tasks']), 'as_of', tasks['as_of'])
for task in tasks['tasks']:
    if task['priority'] in ('P0', 'P1'):
        print(task['id'], task['status'], task['research_objective'][:100])
pdf_names = (
    ('paper2', 'DC KLTN0127 23520355&23521338_LeVanTuan.pdf'),
    ('paper1', 'Paper1_RIVF_2026_Graph_vs_Policy_Adaptive_Sequencing.pdf'),
    ('paper2', 'Paper2_RIVF_2026_Prerequisite_Aware_Knowledge_Tracing.pdf'))
proof = []
for folder, name in pdf_names:
    repo = root / folder / name
    user = Path('C:/Users/AmaDev/Desktop') / name
    digests = {}
    for label, path in (('repository', repo), ('user_provided', user)):
        if path.is_file():
            with path.open('rb') as stream:
                digests[label] = dict(path=str(path), sha256=hashlib.file_digest(stream, 'sha256').hexdigest(),
                                      size_bytes=path.stat().st_size)
        else:
            digests[label] = None
    same = (digests['repository'] is not None and digests['user_provided'] is not None
            and digests['repository']['sha256'] == digests['user_provided']['sha256'])
    proof.append(dict(name=name, inputs=digests, identical_bytes=same))
(out / 'pdf-identity.json').write_text(json.dumps(proof, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('PDF identities', [(record['name'], record['identical_bytes']) for record in proof])
