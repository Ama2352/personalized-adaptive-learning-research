"""Kiểm độc lập từ raw18gzip đã accepted, không dùng hàm analyzer/model."""
from pathlib import Path
from collections import Counter
import gzip
import hashlib
import json

ROOT = Path(__file__).resolve().parents[4]
P = Path(__file__).resolve().parent
sha = lambda raw: hashlib.sha256(raw).hexdigest()
outer = P/'prediction-mastery-native-outer03/final.json'
assert sha(outer.read_bytes()) == '81cf9dd9df724338d6c8d57e01be16b5d2120d27b9730c186b5eb539803e4594'
assert json.loads(outer.read_bytes())['status'] == 'ACCEPTED_FIXED_HISTORY_MASTERY_TRACE_ONLY'
run_path = P/'prediction-mastery-trace-attempt03/worker_run.json'
assert sha(run_path.read_bytes()) == '891a69a3546599782e530d04c3fa29b53fd832f130399404fe159a5fcab2b178'
run = json.loads(run_path.read_bytes()); nodes = run['node_order']; pairs = {}
for item in run['completed_trajectories']:
    path = run_path.parent/item['trace_file']
    assert sha(path.read_bytes()) == item['trace_sha256']
    count = 0
    with gzip.open(path,'rb') as stream:
        while True:
            line = stream.readline(32769)
            if not line: break
            assert len(line) <= 32768 and line.endswith(b'\n')
            row = json.loads(line); key = row['seed'],row['profile'],row['event_id']
            group = pairs.setdefault(key,{})
            assert row['variant'] not in group
            group[row['variant']] = row; count += 1
    assert count == 120
assert len(pairs) == 1080 and all(set(g)=={'graph_package','empty_graph_package'} for g in pairs.values())
cells = Counter(); directions = Counter(); witnesses = {}; M_events = 0
for key, group in sorted(pairs.items(), key=lambda kv:(kv[0][0],kv[0][1],int(kv[0][2]))):
    f,e = group['graph_package'],group['empty_graph_package']; changed = False
    for index,(a,b) in enumerate(zip(f['native_state'],e['native_state'])):
        ga = a[0]>=1250., a[1]<=.55
        gb = b[0]>=1250., b[1]<=.55
        ma,mb = all(ga),all(gb)
        assert list(ga)+( [ma] ) == a[2:] and list(gb)+[mb] == b[2:]
        code = ''.join(str(int(v)) for v in (ga[0]!=gb[0],ga[1]!=gb[1],ma!=mb))
        cells[code] += 1; changed |= ma!=mb
        if code=='010':
            assert not ga[0] and not gb[0] and not ma and not mb
            directions['pi_only_full_pass' if ga[1] else 'pi_only_empty_pass'] += 1
        if code=='101':
            assert ga[1] and gb[1]
            directions['M_full_true' if ma else 'M_empty_true'] += 1
        if code in ('010','101') and code not in witnesses:
            witnesses[code] = dict(seed=key[0],profile=key[1],event_id=key[2],concept=nodes[index],
                full_estimated_theta=a[0],empty_estimated_theta=b[0],full_pi_task=a[1],empty_pi_task=b[1],full_native_M=ma,empty_native_M=mb,
                selection_rule='first chronological seed/profile/event/concept occurrence of this boolean cell; not chosen by outcome gain')
    M_events += int(changed)
summary_path = P/'prediction-mastery-analysis-attempt01/summary.json'
assert sha(summary_path.read_bytes()) == '625095a6421b050f0592e9aecfa4767690ed863d3a5489a414a7b614fb3dde38'
summary = json.loads(summary_path.read_bytes())['groups'][0]
assert dict(cells) == {r['signature']:r['count'] for r in summary['joint_predicate_change_cells'] if r['count']}
assert M_events == summary['M_any_events'] == 90
assert sum(cells.values()) == 30240 and cells['010']==3428 and cells['101']==90 and cells['000']==26722
result = dict(status='INDEPENDENT_RAW_BOOLEAN_MECHANISM_RECONCILED',cells=dict(cells),directions=dict(directions),
              M_events=M_events,concept_pairs=30240,witnesses=witnesses,raw_gzip_crc_verified=18,
              native_model_calls=0,oracle_reads=0,new_independent_N=0,
              scope_vi='Estimated model states and native AND rule only; no latent truth, calibration accuracy, causal learning benefit or independent learner samples.')
with (P/'native_mastery_gates_crosscheck01.json').open('x',encoding='utf-8',newline='\n') as stream:
    json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
print(json.dumps(result,ensure_ascii=False))
