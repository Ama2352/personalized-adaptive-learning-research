"""Đóng cache check đã chạy, không rerun/model; GitHEAD chỉ qua evidencewriter."""
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[4]
PREP=Path(__file__).resolve().parent
WORK=PREP/'a0-a1-cached-export-check01'
RUN='a0-a1-cached-export-check-20261110-01'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert Path(sys.prefix).resolve()==ROOT/'.venv'
    result=json.loads((WORK/'result.json').read_bytes())
    assert result['status']=='VERIFIED_84_CACHED_A0_A1_MATCHED_EXPORTS_ENGINEERING_ONLY'
    assert result['rows']==84 and result['learners']==1 and result['exact_K_y_chronology']is True
    assert result['input_before']==result['input_after'] and result['elapsed_seconds']<3
    assert result['new_model_calls']==0 and result['canonical_metrics_recomputed']is False and result['efficacy_claim']is False
    assert all(sha(ROOT/name)==digest for name,digest in result['input_before'].items())
    copies={'cached_check.py':PREP/'check_a0_a1_cached_exports01.py','result.json':WORK/'result.json',
        'stdout.log':WORK/'stdout.log','stderr.log':WORK/'stderr.log','archiver.py':Path(__file__).resolve()}
    inventory={alias:dict(source=path.relative_to(ROOT).as_posix(),sha256=sha(path),bytes=path.stat().st_size) for alias,path in copies.items()}
    assert sum(v['bytes'] for v in inventory.values())<128*1024
    references=dict(result['input_before'])
    for name in ('research_tracking/runs/akt-public-selected-resume-20261110-01/manifest.json',
                 'research_tracking/runs/a1-expert-selected-engineering-20261110-01/manifest.json',
                 'src/knowledge_tracing/gam_kt/evaluation.py'):
        references[name]=sha(ROOT/name)
    with (PREP/'a0_a1_cached_check_inventory_before01.json').open('x',encoding='utf-8') as stream:
        json.dump(dict(copies=inventory,raw_input_reference_sha256=references),stream,ensure_ascii=False,indent=2);stream.write('\n')
    sys.path.insert(0,str(ROOT/'src'))
    from knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle
    note=('# A0/A1 cached raw selection exports\n\n'
        '84K/y/chronology và causal geometry khớp, backbone/numerical recipe metadata khớp. '
        '84FP32probabilities khác bits, maxabsdelta9,149312973022461e-5 và meanabsdelta2,5654122942969914e-5. '
        'Một selection learner, chỉ engineering output-difference witness; không efficacy, mastery, bootstrap hoặc RQcompletion. '
        'Canonical LL/Brier recompute được bỏ qua vì reporter cần NumPy/Pandas/sklearn, không thay bằng công thức tự viết. '
        'Không rerun model hoặc đọc checkpoint. Native84CSV chỉ tham chiếuSHA, không copy lại.\n')
    metadata=dict(kind='CACHED_A0_A1_ENGINEERING_EXPORT_DIFFERENCE',rows=84,learners=1,
        changed_FP32_probabilities=result['changed_probability_FP32_bit_count'],
        maximum_absolute_probability_delta=result['maximum_absolute_probability_delta'],
        mean_absolute_probability_delta=result['mean_absolute_probability_delta'],new_model_calls=0,new_independent_N=0,
        metric_recompute_skipped=True,efficacy_claim=False,cache_check_cap_seconds=3)
    sources=list(dict.fromkeys([*copies.values(),*(ROOT/name for name in references)]))
    with record_evidence_run(ROOT,RUN,metadata=metadata,sources=sources,note=note) as directory:
        checked={}
        for alias,path in copies.items():
            raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==inventory[alias]['sha256']
            with (directory/alias).open('xb') as stream:stream.write(raw)
            assert sha(directory/alias)==sha(path)==inventory[alias]['sha256']
            checked[alias]=dict(inventory[alias],copy_sha256=sha(directory/alias),source_after_sha256=sha(path))
        (directory/'copy_inventory.json').write_bytes((json.dumps(checked,ensure_ascii=False,indent=2)+'\n').encode())
        (directory/'reference_sources.json').write_bytes((json.dumps(references,ensure_ascii=False,indent=2)+'\n').encode())
        assert all(sha(ROOT/name)==digest for name,digest in references.items())
    out=ROOT/'research_tracking/runs'/RUN
    verified=verify_evidence_bundle(out);assert verified['artifacts']==9
    print(json.dumps(dict(verification=verified,manifest_sha256=sha(out/'manifest.json'),new_model_or_test_calls=0)))


if __name__=='__main__':main()
