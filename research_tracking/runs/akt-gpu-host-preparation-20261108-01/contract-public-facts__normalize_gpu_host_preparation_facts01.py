"""Chỉ chuẩn hóa stored CPU facts; không probe/import hook/remote mới."""
import hashlib
import json
from pathlib import Path

W = Path(__file__).resolve().parent


def main():
    names = ('actual-startup-facts02.json', 'actual-startup-facts03.json', 'startup-facts01-failure.json')
    raw = {name: (W / name).read_bytes() for name in names}
    values = {name: json.loads(body) for name, body in raw.items()}
    for name in names[:2]:
        row = values[name]
        assert row['status'] == 'ACTUAL_STARTUP_SOURCE_FACTS_NO_EXECUTION_OR_APPROVAL'
        assert row['normal_startup_executed'] is False
        assert row['model_imports'] == row['gpu_queries'] == row['installs'] == 0
    failure = values[names[2]]
    assert failure['status'] == 'REJECTED_STARTUP_FACTS01_NO_NORMAL_STARTUP'
    assert 'regular startup source required' in failure['error']['evalue']
    two, three = values[names[0]], values[names[1]]
    value = dict(role='NORMALIZED_EXISTING_ACTUAL_CPU_STARTUP_SOURCE_FACTS_NOT_GPU_AUDIT',
        input_sha256={name: hashlib.sha256(body).hexdigest() for name, body in raw.items()},
        facts02=two, facts03=three,
        failure01=dict(status=failure['status'], exception='ValueError',
            reason='regular startup source required',
            scope_vi='Guard từ chối system symlink trước output; giữ raw private traceback tại workingdir, chỉ archive normalized failure.'),
        new_probes_or_remote_calls=0, hook_normalstartup_model_GPU_install_calls=0,
        limitations_vi=['Facts được đo trên CPU trước hardware switch, không fresh GPU facts.',
            'Không execute/import hooks; no-site prefix/usr chưa là normal target-prefix proof.',
            'Review manifest chỉ cho later matching fresh preflight; không blanket symlink exception.'])
    output = W / 'gpu-host-preparation-public-facts01.json'
    body = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()
    with output.open('xb') as stream: stream.write(body)
    assert all((W / name).read_bytes() == body for name, body in raw.items())
    print(json.dumps(dict(status='NORMALIZED_STORED_FACTS_ONLY_NO_PROBE', output=output.name,
        bytes=len(body), sha256=hashlib.sha256(body).hexdigest(), inputs_prepost_equal=True)))


if __name__ == '__main__': main()
