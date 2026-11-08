"""Đóng gói nhỏ lượt66 metadata đã chạy; không chạy lại tests/model."""
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
RUN = 'cgakt-research-condition-engineering-20261109-01'
sha = lambda raw: hashlib.sha256(raw).hexdigest()
assert Path(sys.prefix).resolve() == ROOT/'.venv'
assert not (ROOT/'research_tracking/runs'/RUN).exists()
result = json.loads((PREP/'graph-condition-pure01/result.json').read_bytes())
assert result['status'] == 'ACCEPTED_66_METADATA_CONDITION_CASES_NOT_MODEL'
assert result['counts'] == dict(tests=66,failures=0,errors=0,skipped=0)
assert result['source_before'] == result['source_after']
assert all(sha((ROOT/n).read_bytes()) == h for n,h in result['source_before'].items())
paths = [ROOT/'src/knowledge_tracing/akt/research_graph_condition.py',
         ROOT/'tests/akt/test_research_graph_condition.py',
         ROOT/'docs/thesis_recovery/26_ADOPTED_MINIMAL_CGAKT_RECIPE_V1.md',
         ROOT/'research_tracking/reports/cgakt_research_condition_readiness_20261109.md',
         PREP/'run_graph_condition_pure01.py', Path(__file__).resolve(),
         *[PREP/'graph-condition-pure01'/n for n in ('result.json','pytest.log','junit.xml')]]
payloads = {}
for path in paths:
    assert path.is_file() and path.is_relative_to(ROOT) and not path.is_symlink()
    assert path.stat().st_size <= 262144
    payloads[path] = path.read_bytes()
inventory = [dict(source=p.relative_to(ROOT).as_posix(),bytes=len(raw),sha256_before=sha(raw)) for p,raw in payloads.items()]
assert sum(map(len,payloads.values())) <= 1024**2
sys.path.insert(0,str(ROOT/'src'))
from knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle
note = '''# Condition CG-AKT nghiên cứu — nghiệm thu metadata

66PASS/0FES; dữ liệu test dựng sẵn, không artifact/corpus/model/solver thực.
Chỉ admission/kwargs conversion/phase lineage; chưa context/forward/training RQ3.
copy_inventory.json giữ SHA trước/sau, source_binding.json giữ deps không copy lại.
Log/JUnit và report nguyên byte; integrity completed không là efficacy claim.
'''
with record_evidence_run(ROOT,RUN,metadata=dict(kind='CGAKT_RESEARCH_CONDITION_METADATA_NOT_MODEL',counts=result['counts']),sources=paths,note=note) as out:
    for i,(path,raw) in enumerate(payloads.items()):
        target = out/f'{i:02d}__{path.name}'
        target.write_bytes(raw)
        assert sha(path.read_bytes()) == sha(target.read_bytes()) == inventory[i]['sha256_before']
        inventory[i].update(copy=target.name,sha256_after_copy=sha(target.read_bytes()))
    (out/'copy_inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (out/'source_binding.json').write_text(json.dumps(result['source_before'],ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
directory = ROOT/'research_tracking/runs'/RUN
verified = verify_evidence_bundle(directory)
assert verified['artifacts'] == 13
print(json.dumps(dict(**verified,manifest_sha256=sha((directory/'manifest.json').read_bytes()),run_id=RUN)))
