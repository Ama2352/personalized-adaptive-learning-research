"""Đo kỹ thuật prefix stream10k target trên cachecalibration, không model."""
import cProfile
import importlib.util
import io
import itertools
import json
from pathlib import Path
import pstats
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('calibration_prep',ROOT/'scripts/akt/prepare_junyi_calibration_data.py')
prep=importlib.util.module_from_spec(spec)
spec.loader.exec_module(prep)
args=SimpleNamespace(mode='profile',max_seconds=60,max_rss_mib=640,max_output_mib=160)
output=ROOT/'artifacts/akt/junyi-cohorts/outer4-calibration-full-20261117-01'
guard=prep.Budget(args,HERE,output)
guard.thread.start()
try:
    from knowledge_tracing.akt.config import DataPaths
    from knowledge_tracing.akt.research_junyi_calibration import _expected_rows
    from knowledge_tracing.akt.research_junyi_data import iter_junyi_phase_learners
    view,_,_,_,_=prep.frozen_inputs()
    prepared=prep.load(HERE/'PREPARED.json')
    paths=DataPaths(**{k:ROOT/v for k,v in prepared['data_paths'].items()})
    learners=iter_junyi_phase_learners(paths,view,fetch_rows=2000)
    rows=_expected_rows(learners,view,max_targets=1621484,max_learner_events=13491)
    profile=cProfile.Profile()
    profile.enable()
    try:
        n=sum(1 for _ in itertools.islice(rows,10000))
    finally:
        rows.close()
        learners.close()
        profile.disable()
    assert n==10000
    text=io.StringIO()
    stats=pstats.Stats(profile,stream=text).sort_stats('cumulative')
    stats.print_stats(35)
    (HERE/'profile01.txt').write_text(text.getvalue(),encoding='utf-8')
    prep.write_new(HERE/'PROFILE.json',dict(status='BOUNDED_TECHNICAL_PROFILE_ONLY',targets=n,
        total_profile_seconds=stats.total_tt,full_population_coverage=False,
        scope_vi='Đọc10000targetđầu từcalibrationcacheđểđoCPU. Khôngcalibrationfit/prediction và không gọi10kđó là populationđầyđủ.'))
finally:
    resource=guard.close()
    prep.write_new(HERE/'profile-RESOURCES.json',resource)
print(json.dumps(dict(targets=n,profile_seconds=stats.total_tt,resources=resource)))
