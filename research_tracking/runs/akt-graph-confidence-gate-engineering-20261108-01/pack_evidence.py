"""Đóng bằng chứng A2/A3 đã kiểm; không chạy lại tests/model."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[4]
PREP=Path(__file__).resolve().parent
RUN='akt-graph-confidence-gate-engineering-20261108-01'
REPORT=ROOT/'research_tracking/reports/akt_graph_confidence_gate_readiness_20261108.md'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))


def main():
    assert Path(sys.prefix).resolve()==ROOT/'.venv'
    production={'src/knowledge_tracing/akt/graph_prototype.py':'9fc6b8271da503ce16d25147a320bf0ffb9312e5416abae40fbb034f26d3157a',
                'tests/akt/test_graph_prototype.py':'17cdfe58dfdbb2e3c4eaba05f62020e3b1289e6a06a69b35b9eddca9af5e09bd'}
    for f,h in production.items():assert sha(ROOT/f)==h
    last=read(PREP/'attempt03/receipt.json')
    assert last['status']=='PASS_TARGETED_TOY_FORWARD_BACKWARD_ONLY'
    assert last['counts']==dict(tests=43,failures=0,errors=0,skipped=0)
    assert last['source_before']==last['source_after']==production
    receipts=[read(PREP/f'attempt{i:02d}/receipt.json') for i in (1,2,3)]
    total=sum(x['controller_seconds'] for x in receipts)
    assert abs(total-last['cumulative_seconds'])<1e-8 and total<=120
    assert all(x['child_reaped'] and x['optimizer_steps']==0 for x in receipts)
    for i,row in enumerate(receipts,1):
        suites=list(ET.parse(PREP/f'attempt{i:02d}/pytest.xml').getroot().iter('testsuite'))
        assert {k:sum(int(s.get(k,0)) for s in suites) for k in ('tests','failures','errors','skipped')}==row['counts']
    peer=PREP/'peer-review-graph-agent.json'
    assert sha(peer)=='594069e8abaa1cf5d2ff4a05f1e7bfdaa5fea895f63467473e22f5c7a92a0887'
    pairs=[(ROOT/f,Path(f).name) for f in production]
    pairs.extend((PREP/n,n) for n in ('graph_prototype.before.py','test_graph_prototype.before.py',
        'run_bounded_tests.py','controller_postattempt02.py','peer-review-graph-agent.md',
        'peer-review-graph-agent.json','peer_review_graph_agent.py'))
    pairs.extend((PREP/f'attempt{i:02d}'/n,f'attempt{i:02d}__'+n) for i in (1,2,3)
        for n in ('receipt.json','source_before.json','graph_prototype.py','test_graph_prototype.py','stdout.log','stderr.log','pytest.xml'))
    pairs.extend([(PREP/'attempt03/controller.py','attempt03__controller.py'),(REPORT,REPORT.name),
                  (Path(__file__),'pack_evidence.py')])
    assert len({n for _,n in pairs})==len(pairs)
    assert sum(p.stat().st_size for p,_ in pairs)<4*1024*1024
    before=[dict(source=p.relative_to(ROOT).as_posix(),copy=n,bytes=p.stat().st_size,sha256=sha(p)) for p,n in pairs]
    count=int(os.environ.get('GIT_CONFIG_COUNT','0'))
    os.environ.update({f'GIT_CONFIG_KEY_{count}':'safe.directory',f'GIT_CONFIG_VALUE_{count}':ROOT.as_posix(),'GIT_CONFIG_COUNT':str(count+1)})
    sys.path.insert(0,str(ROOT/'src'))
    from knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle
    sources=[p for p,_ in pairs]
    sources.extend(ROOT/f for f in ('src/knowledge_tracing/graph_context.py','src/knowledge_tracing/graph_augmentation.py',
        'src/knowledge_tracing/akt/simulator_data.py','src/knowledge_tracing/akt/model.py','artifacts/akt/dependencies/upstream/akt.py'))
    note=('# AKT confidence/gate: bằng chứng engineering\n\n'
        '43 targeted CPU PASS/0optimizer, tổng39.650895s≤120 qua3lượt; giữ lỗiGit ownership01 vàfixturetrain-shard02. '
        'Không fit/research efficacy/calibratedconfidence hoặc method adoption. Gate24 cũ không cover source mới. '
        '[Báo cáo và giới hạn](../../reports/akt_graph_confidence_gate_readiness_20261108.md). '
        'Copy inventory ghim SHA trước/sau; snapshotcontroller03 actual, bảnpost02 không giả pre-execution.\n')
    with record_evidence_run(ROOT,RUN,metadata=dict(kind='A0_A3_TOY_FORWARD_BACKWARD_ENGINEERING',targeted_tests=43,
        optimizer_steps=0,controller_cumulative_seconds=total,cumulative_cap_seconds=120,
        full_gate_current=False,research_fitted=False,scientific_method_adopted=False),sources=sources,note=note) as directory:
        for p,n in pairs:shutil.copyfile(p,directory/n)
        after=[]
        for row in before:
            assert sha(ROOT/row['source'])==sha(directory/row['copy'])==row['sha256']
            after.append({**row,'sha256_after_copy':sha(directory/row['copy']),'exact_match':True})
        (directory/'copy_inventory_before.json').write_text(json.dumps(before,indent=2)+'\n',encoding='utf-8')
        (directory/'copy_inventory.json').write_text(json.dumps(after,indent=2)+'\n',encoding='utf-8')
    result={**verify_evidence_bundle(directory),'run_id':RUN,'manifest_sha256':sha(directory/'manifest.json'),'copy_pairs':len(pairs)}
    print(json.dumps(result))


if __name__=='__main__':main()
