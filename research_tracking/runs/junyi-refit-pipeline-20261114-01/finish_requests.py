"""Ghim config, cache90 và lineage, xuất request/worker refit để preflight."""
from dataclasses import asdict
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'scripts/akt'), str(ROOT / 'experiments/akt')]
from run_junyi_refit import prepare_inputs
from junyi_staged_io import sha, write_new


def pin(path):
    return dict(path=path.relative_to(ROOT).as_posix(), sha256=sha(path))


def main():
    previous = json.loads((ROOT / 'artifacts/akt/staged/junyi-a3-expert-20261114-03/project/gpu-stage-request.json').read_text())
    data = previous['inputs']
    cache = ROOT / 'artifacts/akt/window-cache/full-refit90-20261114-01'
    encoding = cache.with_suffix('.encoding.json')
    common = dict(selected_cache_root=data['selected_cache_root'], roles=pin(ROOT / data['roles_path']),
        selected_cache_manifest_sha256=data['selected_cache_manifest_sha256'],
        encoding90=pin(encoding), encoding90_receipt=pin(encoding.with_suffix('.receipt.json')),
        encoding80=pin(ROOT / data['encoding_file']), encoding80_receipt=pin(ROOT / data['encoding_receipt']),
        window_cache90=cache.relative_to(ROOT).as_posix(), window_manifest_sha256=sha(cache / 'manifest.json'),
        window_admission=pin(ROOT / 'artifacts/akt/window-cache/full-refit90-cpu-admission-20261114-01.json'))
    plan = json.loads((HERE / 'epoch-plan.json').read_text())
    summaries = {}
    folders = dict(A0='model-export-a0-batch128-20261112-01', A1='model-export-a1-batch128-20261113-01',
                   A2='model-export-a2-batch128-20261114-01', A3='model-export-a3-batch128-20261114-01')
    for variant, folder in folders.items():
        request = dict(phase='junyi_refit90', variant=variant, inputs=common,
            config=pin(HERE / ('config-' + variant.lower() + '.json')), cuda_profile=pin(HERE / 'cuda-profile.json'),
            epoch_plan=pin(HERE / 'epoch-plan.json'),
            selected_index=pin(ROOT / 'experiments/akt/results' / folder / 'MODEL_INDEX.json'),
            lock_file=pin(ROOT / 'artifacts/akt/runtime/modal-linux-cuda.lock.txt'),
            authorization=None, runtime_report=None, gate2_report=None,
            execution_state='CPU_PREPARED_PENDING_CURRENT_GATE_RUNTIME_AND_BUDGET')
        if variant != 'A0':
            request.update(graph=pin(ROOT / previous['graph_file']),
                graph_context_cache90=pin(ROOT / 'artifacts/akt/graph-context-cache/full-refit90-20261114-01' /
                                         (variant.lower() + '-train.sqlite')))
            if variant != 'A1':
                request['confidence'] = pin(ROOT / previous['confidence_file'])
        path = HERE / ('refit-request-' + variant.lower() + '.json')
        write_new(path, request)
        context = prepare_inputs(request)
        condition = context['graph_condition']
        summary = dict(status='PASS_REFIT90_CPU_INPUTS', variant=variant, targets=context['inputs'].targets,
            learners=len(context['inputs'].view.users), vocabulary=len(context['encoding'].native.vocabulary.values),
            input_identity=context['inputs'].identity, encoding90=context['encoding'].identity,
            window_manifest_sha256=context['window_cache'].expected_manifest_sha256,
            condition_identity=None if condition is None else condition.identity,
            graph_cache_identity=None if context['graph_cache'] is None else context['graph_cache'].identity,
            train80_confidence_identity=None if condition is None or condition.confidence is None else condition.confidence.identity,
            frozen_epochs=plan['candidates'][variant]['epochs'], training_performed=False, cuda_initialized=False)
        write_new(HERE / ('input-check-' + variant.lower() + '.json'), summary)
        worker = dict(purpose='refit90', variant=variant, logical_run_id=context['config'].run_id,
            config=json.loads((HERE / ('config-' + variant.lower() + '.json')).read_text()),
            profile=asdict(context['profile']), frozen_epochs=summary['frozen_epochs'], refit_request=pin(path))
        write_new(HERE / ('worker-' + variant.lower() + '.json'), worker)
        summaries[variant] = summary
        print(json.dumps(dict(variant=variant, status=summary['status'])), flush=True)
    assert len({row['input_identity'] for row in summaries.values()}) == 1
    assert len({row['encoding90'] for row in summaries.values()}) == 1
    assert len({row['window_manifest_sha256'] for row in summaries.values()}) == 1
    assert summaries['A2']['train80_confidence_identity'] == summaries['A3']['train80_confidence_identity']
    write_new(HERE / 'prepared-refit-matrix.json', dict(status='PASS_FOUR_REFIT_CPU_INPUTS', models=summaries,
        total_epochs=sum(row['frozen_epochs'] for row in summaries.values()), neural_training_performed=False,
        gate_cuda_verified=False, cloud_spending_usd=0))


if __name__ == '__main__':
    main()
