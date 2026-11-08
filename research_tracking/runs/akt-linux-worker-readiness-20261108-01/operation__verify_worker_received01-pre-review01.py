"""Kiểm read-only raw worker; không import model hoặc chạy lại worker."""
import hashlib
import json
from pathlib import Path

W = Path(__file__).resolve().parent
R = W / 'received-cpu-worker-evidence01'
G = W / 'received-linux-gate24'
OUT = W / 'worker-independent-readonly-check01.json'


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    acceptance = load(R / 'acceptance.json')
    assert acceptance['files'] == len(acceptance['copies']) == 32
    for entry in acceptance['copies']:
        p = R / entry['path']
        assert p.resolve().is_relative_to(R.resolve()) and not p.is_symlink()
        assert sha(p) == entry['sha256_before_copy'] == entry['sha256_after_copy']
        assert p.stat().st_size == entry['bytes']
    phase = load(R / 'linux-cpu-dummy-execution-20261108-01/result.json')
    prep = load(R / 'linux-cpu-dummy-preparation-20261108-01/result.json')
    native = load(R / 'experiments/akt/results/ctx-linux-20261108-01/manifest.json')
    watchdog = load(R / 'experiments/akt/results/ctx-linux-20261108-01/watchdog-resources.json')
    context = load(R / 'artifacts/akt/synthetic/ctx-linux-20261108-01/worker-context.json')
    config = load(R / 'linux-cpu-dummy-preparation-20261108-01/execution-config.json')
    auth = load(R / 'linux-cpu-dummy-execution-20261108-01/authorization.json')
    gate = load(G / 'linux-cpu-validation-gate-20261108-03/result.json')
    assert phase['status'] == 'ACCEPTED_NATIVE_CPU_DUMMY_ENGINEERING_ONLY'
    assert prep['status'] == 'PREPARED_CPU_DUMMY_NOT_EXECUTION_AUTHORIZED'
    assert phase['preparation_result_sha256'] == sha(R / 'linux-cpu-dummy-preparation-20261108-01/result.json')
    assert phase['gate_result_sha256'] == sha(G / 'linux-cpu-validation-gate-20261108-03/result.json')
    assert phase['source_sha256_before'] == gate['source_sha256_before']
    assert phase['native_manifest_sha256'] == sha(R / 'experiments/akt/results/ctx-linux-20261108-01/manifest.json')
    assert phase['watchdog_resources_sha256'] == sha(R / 'experiments/akt/results/ctx-linux-20261108-01/watchdog-resources.json')
    identity = native['identity']
    assert identity['config_sha256'] == auth['config_sha256'] == sha(R / 'linux-cpu-dummy-preparation-20261108-01/execution-config.json')
    assert identity['worker_context_sha256'] == sha(R / 'artifacts/akt/synthetic/ctx-linux-20261108-01/worker-context.json')
    assert identity['worker_context_inputs_sha256'] == context['input_hashes']
    assert identity['lock_sha256'] == gate['lock_sha256']
    assert identity['runtime_report_sha256'] == gate['runtime_sha256']
    assert identity['source'] == auth['identity']['source']
    for name, value in context['input_hashes'].items():
        if (R / name).is_file():
            assert sha(R / name) == value
    assert native['gate_records']['gate2']['report_sha256'] == sha(G / 'artifacts/akt/preflight/gate2-evidence-20261108-linux-native-24.json')
    assert native['gate_records']['gate2']['pointer_sha256'] == sha(G / 'artifacts/akt/preflight/gate2-current.json')
    assert config['device'] == 'cpu' and config['phase'] == 'smoke' and config['graph'] is False
    assert config['max_steps'] == 2 and config['max_targets_per_side'] == 64 and config['max_total_targets'] == 128
    assert config['max_seconds'] == 120 and config['max_wall_seconds'] == 300
    assert config['max_rss_bytes'] == 2 * 1024**3 and config['min_available_ram_bytes'] == 1024**3
    assert native['status'] == 'completed' and watchdog['status'] == 'completed' and watchdog['worker_returncode'] == 0
    assert phase['child_cleanup_accepted'] is True
    assert all(c['returncode'] == 0 and c['cleanup_accepted'] is True for c in phase['children'])
    s = native['summary']
    assert phase['summary'] == s
    t = s['training']
    assert t['optimizer_steps'] == t['parameter_update_steps'] == t['nonzero_gradient_steps'] == 2
    assert t['optimized_target_rows'] == t['processed_target_rows'] == 48 and t['collated_windows'] == 6
    assert s['coverage']['prediction_rows'] == s['coverage']['expected_rows'] == 8
    assert s['coverage']['unseen_rows'] == 0 and s['checkpoint_reload_state_exact'] is True
    assert s['holdout_requested'] is False and s['outer_users_requested'] is False
    assert phase['elapsed_seconds'] < 330 and watchdog['elapsed_seconds'] < 300 and s['elapsed_seconds'] < 120
    assert t['resource']['peak_rss_bytes'] < config['max_rss_bytes']
    assert min(x['system_available_ram_bytes'] for x in t['resource']['samples']) > config['min_available_ram_bytes']
    omitted = [name for name in phase['native_output_hashes'] if not (R / name).is_file()]
    result = {'status': 'INDEPENDENT_READONLY_CPU_WORKER_ENGINEERING_CHECK_PASS_PENDING_PARENT_REVIEW',
              'verified_text_files': 32, 'text_bytes': sum(x['bytes'] for x in acceptance['copies']),
              'acceptance_sha256': sha(R / 'acceptance.json'), 'execution_result_sha256': sha(R / 'linux-cpu-dummy-execution-20261108-01/result.json'),
              'native_manifest_sha256': phase['native_manifest_sha256'], 'source_inventory_count': len(phase['source_sha256_before']),
              'source_context_config_auth_runtime_lock_gate_bindings_verified': True,
              'optimizer_steps': 2, 'parameter_update_steps': 2, 'optimized_target_rows': 48, 'collated_windows': 6,
              'prediction_rows': 8, 'unseen_rows': 0, 'checkpoint_reload_state_exact_recorded': True,
              'controller_seconds': phase['elapsed_seconds'], 'watchdog_seconds': watchdog['elapsed_seconds'],
              'native_summary_seconds': s['elapsed_seconds'], 'all_child_cleanup_accepted': True,
              'binary_native_outputs_not_received_in_text_export': omitted,
              'limits': 'Raw JSON/log/hash validation only; no local binary reload or model rerun. Binary durability receipt pending. CPU dummy only; no CUDA/resume/refit/research claims.'}
    with OUT.open('x', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
