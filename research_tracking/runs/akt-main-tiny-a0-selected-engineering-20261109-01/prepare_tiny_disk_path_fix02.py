"""Giữ nguồn01, tạo derivative disk-path cùng request/controller mới đã review."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    original = (PREP / 'run_main_tiny_selected_a0_01.py').read_bytes()
    assert sha(original) == 'a94a712638c5d9bf93beaac3099064c3f5af3168af646b893852a00a761774b0'
    assert original.count(b'psutil.disk_usage(R)') == 1
    fixed = original.replace(b'psutil.disk_usage(R)', b'psutil.disk_usage(str(R))')
    outer = PREP / 'run_main_tiny_selected_a0_02.py'
    request_path = PREP / 'main_tiny_selected_a0_02_request.ROOT.json'
    launcher = PREP / 'launch_tiny_a0_profile02.py'
    assert not any(p.exists() for p in (outer, request_path, launcher))
    request_raw = (PREP / 'main_tiny_selected_a0_01_request.ROOT.json').read_bytes()
    assert sha(request_raw) == 'c58d36961621541b957567195c81e194bf6ca0315e5d7377aa439ea9960b9c74'
    request = json.loads(request_raw)
    for name, field in (('native_config_file', 'native_config_sha256'), ('authorization_file', 'authorization_sha256')):
        assert sha((ROOT / request[name]).read_bytes()) == request[field]
    for name in ('main-tiny-selected-a0-01', 'main-tiny-selected-a0-01-owned'):
        assert not (PREP / name).exists()
    request['source_pins'][outer.relative_to(ROOT).as_posix()] = sha(fixed)
    wire = (json.dumps(request, ensure_ascii=False, indent=2) + '\n').encode()
    profile = (PREP / 'launch_tiny_a0_profile01.py').read_text(encoding='utf-8')
    profile = profile.replace('run_main_tiny_selected_a0_01.py', outer.name)
    profile = profile.replace('a94a712638c5d9bf93beaac3099064c3f5af3168af646b893852a00a761774b0', sha(fixed))
    profile = profile.replace('main_tiny_selected_a0_01_request.ROOT.json', request_path.name)
    profile = profile.replace("args.mode + '01'", "args.mode + '02'")
    profile = profile.replace('ROOT_MAIN_TINY_A0_ACTUAL_FIT_REVIEW01.md', 'ROOT_MAIN_TINY_A0_ACTUAL_FIT_REVIEW02.md')
    inventory = dict(original_outer_sha256=sha(original), derivative_outer_sha256=sha(fixed),
        original_request_sha256=sha(request_raw), derivative_request_sha256=sha(wire),
        config_and_authorization_unchanged=True, native_worker_started_in_original_attempt=False,
        scope_vi='Chỉ chuyển Path thành str ở disk API, thêm pin controller02 vào request. Giữ cap, source177, config/auth và model recipe.')
    with (PREP / 'tiny_disk_path_fix02_inventory.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(inventory, stream, ensure_ascii=False, indent=2)
    for path, raw in ((outer, fixed), (request_path, wire), (launcher, profile.encode())):
        with path.open('xb') as stream:
            stream.write(raw)
        assert path.read_bytes() == raw
    print(json.dumps(inventory, ensure_ascii=False))


if __name__ == '__main__':
    main()
