"""Đóng model11/trainer8 actual, giữ ranh giới compute và fitted baseline."""
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
BUNDLE = ROOT / 'research_tracking/runs/gkt-research-model-trainer-20261110-01'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


receipts = {}
files = []
for stem, count in (('gkt-research-model02', 11), ('gkt-research-training02', 8)):
    outer = PREP / (stem + '-owned') / 'final.json'
    data = json.loads(outer.read_bytes())
    assert data['counts'] == dict(tests=count, failures=0, errors=0, skipped=0)
    assert data['errors'] == []
    assert data['source_before'] == data['source_after']
    assert data['runtime_before'] == data['runtime_after']
    assert data['owned_receipt']['accepted'] and data['owned_receipt']['cleanup_accepted']
    assert data['owned_receipt']['job_active_after_cleanup'] == 0
    receipts[stem] = dict(path=outer.relative_to(ROOT).as_posix(), sha256=sha(outer),
        status=data['status'], counts=data['counts'], elapsed_seconds=data['elapsed_seconds'],
        counters=data['child_result']['counters'], resources=data['child_result'].get('resources'))
    for directory in (PREP/stem, PREP/(stem+'-owned')):
        files.extend(p for p in directory.rglob('*') if p.is_file()
            and 'runtime-temp' not in p.parts and p.suffix in ('.json', '.jsonl', '.xml', '.log'))
for name in ('check_gkt_research_model02.py', 'run_gkt_research_model02.py', 'gkt_research_model02_packet.json',
    'check_gkt_research_training02.py', 'run_gkt_research_training02.py', 'gkt_research_training02_packet.json',
    'GKT_RESEARCH_TRAINER8_SOURCE_HANDOFF02.md', 'gkt_research_training02_ast_pins.json',
    'GKT_NEGATIVE_SECOND_MOMENT_FIX04.md'):
    files.append(PREP/name)
files.extend(p for p in (PREP/'gkt-negative-second-moment-before04').rglob('*') if p.is_file())
files.extend(ROOT/name for name in ('src/knowledge_tracing/gkt/research_model.py',
    'src/knowledge_tracing/gkt/research_training.py', 'tests/gkt/test_research_model.py',
    'tests/gkt/test_research_training.py'))
files.append(Path(__file__).resolve())
files = list(dict.fromkeys(files))
BUNDLE.mkdir(exist_ok=False)
inventory = {p.relative_to(ROOT).as_posix(): dict(sha256=sha(p), bytes=p.stat().st_size) for p in files}
write(BUNDLE/'inventory_before_copy.json', inventory)
for source in files:
    relative = source.relative_to(ROOT)
    if source.is_relative_to(PREP):
        relative = Path('execution') / source.relative_to(PREP)
    target = BUNDLE/relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    assert sha(target) == inventory[source.relative_to(ROOT).as_posix()]['sha256']
write(BUNDLE/'acceptance.json', dict(kind='GKT_research_model_and_trainer_CPU_fixture_acceptance',
    receipts=receipts, separate_physical_tests=19, corpus_fit=False, CUDA=False,
    checkpoint_ready=False, selected_producer_ready=False, fitted_baseline=False))
(BUNDLE/'README.md').write_text(
    '# Nghiệm thu compute GKT model11 và trainer8\n\n'
    'Hai lượt riêng chạy19physical test functions, đều0failures/errors/skips. '
    'Model kiểm causal/preflight/padding/BN/dropout và backward. Trainer thực hiện4Adam steps trên fixtures, '
    'phân biệt64actual optimized target exposures với48confirmed cùng16pending của failure fixture. '
    'Guard second moment âm được kiểm trước compute. '
    'Source/runtime trước–sau khớp, cả hai owned Jobs về0. '
    'Không nghiên cứu fit, chưa checkpoint/research producer/adapter hoặc baseline so sánh đã huấn luyện. '
    'Giữ snapshot trước guard04, actuallogs và nguồn hiện hành.\n', encoding='utf-8')
write(BUNDLE/'manifest.json', dict(kind='GKT_model_and_trainer_engineering',
    outputs_sha256={p.relative_to(BUNDLE).as_posix(): sha(p) for p in BUNDLE.rglob('*') if p.is_file()}))
print('GKT_MODEL11_TRAINER8_BUNDLE_CLOSED',len(files),'inputs')
