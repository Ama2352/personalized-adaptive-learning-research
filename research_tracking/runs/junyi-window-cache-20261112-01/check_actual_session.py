"""Đối chiếu hot session với native windows của cohort Junyi đã ghim."""
from itertools import zip_longest
import json
from pathlib import Path
import sys

from check_actual_bounded import ROOT, equal_record, sha
from knowledge_tracing.akt.research_junyi_engineering import prepare_inputs
from knowledge_tracing.akt.research_junyi_data import iter_junyi_research_windows
from knowledge_tracing.akt.research_junyi_window_cache import JunyiWindowCacheSession


def main():
    evidence = Path(__file__).with_name('actual-bounded-result.json')
    original = json.loads(evidence.read_text(encoding='utf-8'))
    assert all(sha(ROOT/name) == value for name, value in original['source_pins'].items())
    cohort = ROOT/'artifacts/akt/junyi-cohorts/cuda-engineering320x300-20261112-01'
    roles = ROOT/'artifacts/akt/junyi-roles/outer4-research-v1-20261112-01/roles.json'
    views, encoding, learners, options = prepare_inputs(cohort, roles,
        cohort_sha256=original['source_pins'][(cohort/'manifest.json').relative_to(ROOT).as_posix()],
        roles_sha256=original['source_pins'][roles.relative_to(ROOT).as_posix()])
    del learners
    results = {}
    for role, target_count in (('train', 11833), ('selection', 1530)):
        cached = original['role_results'][role]
        session = JunyiWindowCacheSession(ROOT/cached['root'], views[role], encoding,
            cached['source_data_sha256'], target_count, cached['receipt']['manifest_sha256'])
        sentinel = object(); compared = 0
        for native, hot in zip_longest(iter_junyi_research_windows(None, views[role], encoding, **options),
                session.iter_windows(), fillvalue=sentinel):
            assert native is not sentinel and hot is not sentinel
            equal_record(native, hot); compared += 1
        assert compared == session.strict_records_verified
        results[role] = dict(strict_records_verified=session.strict_records_verified,
            native_hot_exact_records_compared=compared, strict_admission_seconds=session.strict_seconds,
            manifest_sha256=cached['receipt']['manifest_sha256'])
    assert all(sha(ROOT/name) == value for name, value in original['source_pins'].items())
    assert 'torch' not in sys.modules
    output = dict(status='ACTUAL_BOUNDED_SESSION_NATIVE_EXACT_ROUNDTRIP_PASS', roles=results,
        source_evidence_sha256=sha(evidence), source_pins=original['source_pins'],
        module_sha256=sha(ROOT/'src/knowledge_tracing/akt/research_junyi_window_cache.py'),
        torch_imported=False, cloud_execution=False, training_performed=False)
    with Path(__file__).with_name('actual-session-roundtrip.json').open('x',encoding='utf-8') as stream:
        json.dump(output,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print(json.dumps(output['roles']),flush=True)


if __name__ == '__main__':
    main()
