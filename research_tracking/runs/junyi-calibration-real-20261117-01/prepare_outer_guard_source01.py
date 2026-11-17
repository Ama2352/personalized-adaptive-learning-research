"""Chuẩn bị nguồncode mới và kiểm A2pins trong process riêng, không model/data."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
FROZEN = ROOT/'artifacts/akt/local-calibration/20261117/calibration-inputs-20261117-01/source'
TARGET = ROOT/'artifacts/akt/local-calibration/20261117/outer-source-guard-release/source'
GUARD = 'src/knowledge_tracing/akt/research_junyi_window_cache.py'
RELEASE = ROOT/'research_tracking/runs/junyi-outer-cache-release-20261117-01/SOURCE_DELTA01.json'
CAP = 4*1024**3


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, payload):
    with (HERE/name).open('x', encoding='utf-8') as stream:
        json.dump(payload, stream, indent=2, ensure_ascii=False)
        stream.write('\n')


def prepare():
    assert not TARGET.exists(), 'New source destination required'
    assert TARGET.absolute() == TARGET.resolve()
    assert TARGET.resolve().is_relative_to((ROOT/'artifacts/akt/local-calibration/20261117').resolve())
    parent = TARGET.parent
    while parent != ROOT:
        assert not parent.is_symlink() and not parent.is_junction(), 'Source destination alias rejected'
        parent = parent.parent
    release = json.loads(RELEASE.read_text())
    relative = {path.relative_to(FROZEN).as_posix() for path in (FROZEN/'src').rglob('*.py')}
    relative.update(release['frozen_files'])
    plan = []
    for name in sorted(relative):
        source = ROOT/name if name == GUARD else FROZEN/name
        assert source.is_file() and not source.is_symlink()
        plan.append(dict(path=name, source=str(source), bytes=source.stat().st_size,
                         sha256=sha(source)))
    total = sum(row['bytes'] for row in plan)
    assert total <= CAP
    assert all(next(row['sha256'] for row in plan if row['path'] == name) == expected
               for name, expected in release['proposed_frozen_plus_one_guard_files'].items())
    write('OUTER_SOURCE_COPY_PLAN01.json', dict(kind='SOURCE_ONLY_COPY_INVENTORY_V1',
        target=str(TARGET), files=plan, total_bytes=total, cap_bytes=CAP))
    for row in plan:
        destination = TARGET/row['path']
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open('xb') as stream:
            stream.write(Path(row['source']).read_bytes())
        assert sha(destination) == row['sha256']
    assert all(sha(FROZEN/name) == expected for name, expected in release['frozen_files'].items())
    write('OUTER_SOURCE_COPY_ACCEPTANCE01.json', dict(status='SOURCE_ONLY_COPY_VERIFIED',
        source=str(FROZEN), target=str(TARGET), copied_files=len(plan), bytes=total,
        copy_plan_sha256=sha(HERE/'OUTER_SOURCE_COPY_PLAN01.json'),
        frozen77_source_files_unchanged=True, model_or_data_copied=False))
    print(json.dumps(dict(status='SOURCE_ONLY_COPY_VERIFIED', files=len(plan), bytes=total)))


def verify():
    assert not any(name.startswith('knowledge_tracing') for name in sys.modules)
    sys.path.insert(0, str(TARGET/'src'))
    from knowledge_tracing.akt.config import PROJECT_ROOT
    from knowledge_tracing.akt.research_junyi_calibration import inference_source_identity
    from knowledge_tracing.response_calibration import PredictionBinding, TemperatureCalibration
    assert PROJECT_ROOT == TARGET
    spec = importlib.util.spec_from_file_location('outer_release_wrapper_actual',
                                                ROOT/'scripts/akt/free_outer_evaluation.py')
    wrapper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wrapper)
    release = json.loads(RELEASE.read_text())
    assert inference_source_identity() == wrapper.NEW_SOURCE
    actual = wrapper.runtime_source_files()
    assert actual == release['proposed_frozen_plus_one_guard_files']
    acceptance_path = HERE/'LOCAL_A2_FIT_ACCEPTANCE100.json'
    accepted = json.loads(acceptance_path.read_text())
    assert accepted['status'] == 'A2_LOCAL_CALIBRATION_INDEPENDENT_DRIVE_READBACK_ACCEPTED'
    assert accepted['account'] == 'honguyenminhsang2005@gmail.com'
    payload = accepted['calibration']
    calibration = TemperatureCalibration.from_payload(payload, binding=PredictionBinding(**payload['binding']))
    assert calibration.identity == accepted['calibration_identity']
    model_index_path = ROOT/'experiments/akt/results/model-export-a2-refit-20261114-01/MODEL_INDEX.json'
    index = json.loads(model_index_path.read_text())
    checkpoint = index['checkpoint_sha256']
    assert checkpoint == calibration.binding.checkpoint_sha256
    receipt = wrapper.build_compatibility_receipt(release['frozen_files'], actual,
        checkpoint_sha256=checkpoint, calibration_identity=calibration.identity)
    provenance = wrapper.validate_compatibility(receipt, checkpoint_sha256=checkpoint,
        calibration_identity=calibration.identity, calibrated_source=calibration.binding.model_source_sha256,
        current_source=inference_source_identity())
    assert 'torch' not in sys.modules
    write('A2_OUTER_SOURCE_COMPATIBILITY01.json', receipt)
    output = dict(status='ACTUAL_SOURCE_FILES_AND_A2_PINS_VERIFIED',
        source_root=str(TARGET), inference_source_identity=inference_source_identity(),
        runtime_files=len(actual), torch_imported=False, predictor_admission_performed=False,
        calibration_identity=calibration.identity, checkpoint_sha256=checkpoint,
        acceptance_sha256=sha(acceptance_path), model_index_sha256=sha(model_index_path),
        wrapper_sha256=sha(ROOT/'scripts/akt/free_outer_evaluation.py'),
        compatibility_receipt_sha256=sha(HERE/'A2_OUTER_SOURCE_COMPATIBILITY01.json'),
        provenance=provenance,
        pending=['numerical CUDA parity', 'actual model/predictor admission', 'outer data preparation/evaluation'])
    write('A2_OUTER_SOURCE_ACTUAL_VERIFY01.json', output)
    print(json.dumps(output))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--prepare', action='store_true')
    options = parser.parse_args()
    prepare() if options.prepare else verify()
