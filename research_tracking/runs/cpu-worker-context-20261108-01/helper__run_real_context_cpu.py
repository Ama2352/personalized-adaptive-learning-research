"""Kiểm local synthetic qua watchdog thật; không dùng dataset thật hoặc cloud."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

root = Path.cwd()
sys.path.insert(0, str(root / 'src'))
count = int(os.environ.get('GIT_CONFIG_COUNT', '0'))
os.environ['GIT_CONFIG_COUNT'] = str(count + 1)
os.environ[f'GIT_CONFIG_KEY_{count}'] = 'safe.directory'
os.environ[f'GIT_CONFIG_VALUE_{count}'] = (root / 'artifacts/akt/dependencies/upstream').as_posix()
os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
os.environ['PYTHONPATH'] = os.pathsep.join([str(root / 'src'), str(root / 'third_party')])
from knowledge_tracing.akt.config import load_config
from knowledge_tracing.akt.context import load_worker_context, context_authorization_identity
from knowledge_tracing.akt.authorization import config_hash, require_authorization

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)

label = 'context-real-cpu-20261108-01'
out = root / 'artifacts/akt/local-tests' / label
out.mkdir(exist_ok=False)
source_dir = root / 'artifacts/akt/synthetic/ctx0801'
preparation = json.loads((source_dir / 'preparation-inventory.json').read_text())
before = preparation['outputs_sha256']
assert all(digest(root / name) == expected for name, expected in before.items())
config_data = json.loads((source_dir / 'config.json').read_text())
assert config_data['execution_enabled'] is False
config_data['execution_enabled'] = True
config_path = out / 'execution-config.json'
write(config_path, config_data)
config = load_config(config_path)
assert config.device == 'cpu' and config.max_steps == 2 and config.max_seconds == 120
assert not config.output_dir.exists()
context_path = source_dir / 'worker-context.json'
context = load_worker_context(context_path, expected_sha256=digest(context_path))
# Actual source/runtime/lock/Gate2 identities: no injected validator or fixture.
identity = context_authorization_identity(config, context)
caps = {key: getattr(config, key) for key in (
    'max_train_users', 'max_val_users', 'max_targets_per_side', 'max_steps',
    'max_seconds', 'max_wall_seconds', 'max_rss_bytes', 'min_available_ram_bytes')}
approval = {'approved': True, 'scope': 'development-inner-only', 'phase': 'smoke',
    'run_id': config.run_id, 'source_commit': config.source_commit,
    'config_sha256': config_hash(config), 'identity': identity, 'caps': caps,
    'approval_reference': 'User 2026-11-08: continue autonomous local engineering; bounded synthetic CPU only, no real data/cloud/full CV/Holdout.'}
approval_path = out / 'authorization.json'
write(approval_path, approval)
require_authorization(config, approval, identity_fn=lambda c: context_authorization_identity(c, context))
command = [sys.executable, '-B', '-m', 'knowledge_tracing.akt.cli', 'smoke',
    '--config', str(config_path), '--authorization', str(approval_path),
    '--context-file', str(context_path), '--context-sha256', context.manifest_sha256]
write(out / 'planned-run.json', {'command': command, 'input_hashes': before,
    'expected': {'train_users': 6, 'validation_users': 1, 'train_targets': 48,
                 'validation_predictions': 8, 'optimizer_steps': 2},
    'limits': caps, 'scope': 'Local actual-guard synthetic CPU lifecycle only'})
started = time.perf_counter()
with (out / 'stdout.log').open('xb') as stdout, (out / 'stderr.log').open('xb') as stderr:
    result = subprocess.run(command, cwd=root, stdout=stdout, stderr=stderr, timeout=320)
write(out / 'execution.json', {'returncode': result.returncode,
    'elapsed_seconds': time.perf_counter() - started, 'command': command})
assert all(digest(root / name) == expected for name, expected in before.items())
if result.returncode:
    print(json.dumps({'status': 'FAILED', 'returncode': result.returncode, 'logs': str(out)}))
    raise SystemExit(result.returncode)
manifest = json.loads((config.output_dir / 'manifest.json').read_text())
assert manifest['status'] == 'completed'
summary = manifest['summary']
assert summary['training']['valid_targets'] == 48
assert summary['training']['optimizer_steps'] == 2
assert summary['checkpoint_reload_state_exact'] is True
assert summary['coverage']['prediction_rows'] == summary['coverage']['expected_rows'] == 8
assert summary['outer_users_requested'] is False and summary['holdout_requested'] is False
assert summary['checkpoint_sha256'] == digest(config.output_dir / summary['selection_checkpoint'])
import duckdb
glob = str(config.output_dir / 'predictions/part-*.parquet')
con = duckdb.connect(':memory:')
schema = con.execute('DESCRIBE SELECT * FROM read_parquet(?)', [glob]).fetchall()
rows = con.execute('SELECT user_id, source_row, exercise, correct, prediction, prediction_kind FROM read_parquet(?) ORDER BY user_id, source_row', [glob]).fetchall()
assert len(rows) == 8 and len({r[0] for r in rows}) == 1
assert len({(r[0], r[1]) for r in rows}) == 8
assert all(0 <= r[4] <= 1 for r in rows)
con.close()
files = {p.relative_to(root).as_posix(): digest(p) for p in config.output_dir.rglob('*') if p.is_file()}
write(out / 'acceptance.json', {'status': 'PASS', 'scope': 'actual Windows CPU watchdog/worker with real guards and toy Parquet inputs',
    'actual_cuda': False, 'research_model_evidence': False, 'input_hashes_unchanged': True,
    'predictions_rows': len(rows), 'prediction_schema': schema,
    'output_hashes': files, 'summary': summary, 'identity': identity})
print(json.dumps({'status': 'PASS', 'output': str(config.output_dir), 'acceptance': str(out / 'acceptance.json')}))
