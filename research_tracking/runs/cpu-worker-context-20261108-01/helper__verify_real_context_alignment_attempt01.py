import csv
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys

root = Path.cwd()
sys.path.insert(0, str(root / 'src'))
import duckdb
from knowledge_tracing.akt.splits import make_inner_split

out = root / 'artifacts/akt/local-tests/context-real-cpu-20261108-01'
result = root / 'experiments/akt/results/ctx0801'
con = duckdb.connect(':memory:')
assignments = con.execute('SELECT * FROM read_parquet(?)', [str(root / 'artifacts/akt/synthetic/ctx0801/assignments.parquet')]).fetchdf()
split = make_inner_split(assignments, outer_fold=0, seed=42)
assert len(split.inner_train_users) == 6 and len(split.inner_val_users) == 1
manifest = json.loads((result / 'manifest.json').read_text())
assert manifest['identity']['split_hash'] == split.split_hash
pred = con.execute('SELECT user_id,source_row,exercise,time_done,correct,prediction,prediction_kind,fold,checkpoint_id,history_available FROM read_parquet(?) ORDER BY user_id,time_done,source_row', [str(result / 'predictions/part-*.parquet')]).fetchall()
source = con.execute('SELECT user_id,source_row,exercise,time_done,correct FROM read_parquet(?) ORDER BY user_id,time_done,source_row', [str(root / 'artifacts/akt/synthetic/ctx0801/canonical/events.parquet')]).fetchall()
expected = [r for r in source if r[0] in split.inner_val_users]
assert [r[:5] for r in pred] == expected
assert len(pred) == 8 and all(r[6] == 'fitted' and r[7] != 0 and r[8] == manifest['summary']['checkpoint_sha256'] for r in pred)
assert [r[9] for r in pred] == list(range(8))
assert len([r for r in source if r[0] in split.inner_train_users]) == 48
assert manifest['summary']['training']['collated_windows'] == 6
con.close()
with (out / 'toy_predictions.csv').open('x', newline='', encoding='utf-8') as stream:
    writer = csv.writer(stream)
    writer.writerow(['user_id','source_row','exercise','time_done','correct','prediction','prediction_kind','fold','checkpoint_id','history_available'])
    writer.writerows(pred)
payload = {'status':'PASS','scope':'Synthetic export chronological alignment and deterministic split reconstruction; no model rerun',
    'split': asdict(split), 'training_targets':48, 'validation_targets':8,
    'alignment_matches_original_toy_labels':True,'history_counts_exact_0_to_7':True,
    'outer_fold0_excluded':True,'checkpoint_identity_matches':True,
    'prediction_csv_sha256':hashlib.sha256((out / 'toy_predictions.csv').read_bytes()).hexdigest()}
with (out / 'alignment.json').open('x', encoding='utf-8') as stream: json.dump(payload,stream,ensure_ascii=False,indent=2)
print(json.dumps(payload))
