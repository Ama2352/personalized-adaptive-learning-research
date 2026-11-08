"""Cold GPU-host bootstrap ONLY. No pip/normal startup/install/device/model calls.

Reference: ../COLD_GPU_HOST_PREPARATION_CONTRACT01.md. Source/packet are staged
OUTSIDE absent ROOT. Descriptor is discovery pending startup+pip review, not
install authority, T4 identification, CUDA readiness or hostile-host attestation.
"""
import argparse
import ast
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import shutil
import signal
import stat
import struct
import subprocess
import sys
import sysconfig
import time
import traceback

ROOT_TEXT = '/content/KLTN_GPU08_20261108_01'
STAGING_TEXT = '/content/KLTN_GPU10_COLD_BOOTSTRAP_20261108_01'
ROOT = Path(ROOT_TEXT); VENV = ROOT / '.venv'; BASE = Path('/usr/bin/python3')
STAGING = Path(STAGING_TEXT); ATTEMPT = STAGING / 'bootstrap-attempt02'
MODE = 'GPU_HOST_CUDA_HIDDEN_BOOTSTRAP_EMPTY'
PENDING = 'FRESH_EMPTY_VENV_DISCOVERY_PENDING_STARTUP_AND_PIP_REVIEW'
CAP_SECONDS = 30; CHILD_SECONDS = 24; CAP_BYTES = 128 * 1024**2
FLOOR_FREE = 30 * 1024**3; CAP_LOGS = 4 * 1024**2


def digest(raw): return hashlib.sha256(raw).hexdigest()


def is_sha(value):
    return type(value) is str and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def child_time_remaining(started, now):
    if not all(type(x) in (int, float) and math.isfinite(x) for x in (started, now)) or now < started:
        raise ValueError('invalid child deadline clock')
    remaining = CHILD_SECONDS - (now - started)
    if remaining <= 0: raise TimeoutError('24s child deadline; reserve6s cleanup/posthash')
    return remaining


def read_regular(path, limit):
    if path.is_symlink() or not stat.S_ISREG(path.stat().st_mode):
        raise ValueError('bounded regular input required')
    with path.open('rb') as stream: raw = stream.read(limit + 1)
    if len(raw) > limit: raise ValueError('input byte ceiling')
    return raw


def absent_root(path):
    if path.exists() or path.is_symlink():
        raise FileExistsError('fixed ROOT must be absent; no repair/delete/reuse')
    if path.resolve() != path or not path.parent.is_dir():
        raise ValueError('fixed physical parent required; no indirect symlink')


def validate_cfg(raw):
    rows = [line.strip().lower() for line in raw.decode('utf-8').splitlines()]
    if rows.count('include-system-site-packages = false') != 1 or any(
            'include-system-site-packages' in x and x != 'include-system-site-packages = false' for x in rows):
        raise ValueError('system site packages must be disabled in actual cfg')


def validate_packet(packet):
    expected = dict(schema_version=1, role='COLD_BOOTSTRAP_POLICY_NOT_HOST_FACTS', mode=MODE,
        target_root=ROOT_TEXT, base_python='/usr/bin/python3', required_implementation='cpython',
        required_machine='x86_64', pointer_bits=64, gil_disabled=False,
        overall_seconds=30, child_seconds=24, workspace_bytes=CAP_BYTES, log_bytes=CAP_LOGS,
        minimum_free_bytes=FLOOR_FREE)
    if type(packet) is not dict or set(packet) != set(expected): raise ValueError('strict reviewed policy packet required')
    if any(type(packet[k]) is not type(v) or packet[k] != v for k, v in expected.items()):
        raise ValueError('policy cannot override fixed paths/mode/resource/ABI boundaries')
    return packet


def abi_facts():
    return dict(implementation=sys.implementation.name, python_version=platform.python_version(),
        python_full=sys.version, cache_tag=sys.implementation.cache_tag, system=platform.system(),
        machine=platform.machine(), pointer_bits=struct.calcsize('P') * 8,
        soabi=sysconfig.get_config_var('SOABI'), extension_suffix=sysconfig.get_config_var('EXT_SUFFIX'),
        gil_disabled=bool(sysconfig.get_config_var('Py_GIL_DISABLED')),
        libc=list(platform.libc_ver()), executable=sys.executable, prefix=sys.prefix, base_prefix=sys.base_prefix,
        isolated=sys.flags.isolated, no_site=sys.flags.no_site, bytecode_disabled=sys.dont_write_bytecode)


def validate_abi(facts, packet):
    if (facts['system'] != 'Linux' or facts['implementation'] != packet['required_implementation']
            or facts['machine'] != packet['required_machine'] or type(facts['pointer_bits']) is not int
            or facts['pointer_bits'] != 64 or facts['gil_disabled'] is not False
            or facts['isolated'] != 1 or facts['no_site'] != 1 or facts['bytecode_disabled'] is not True
            or 'venv' not in sysconfig.get_scheme_names()):
        raise ValueError('actual no-site Linux CPython standard-GIL ABI required before creation')
    # Python patch/minor/glibc are recorded, not silently copied from historical CPU-v3.


def host_indication(environ, nodes):
    if environ.get('COLAB_TPU_ADDR'): raise ValueError('TPU host is outside this explicit GPU-host mode')
    value = dict(colab_gpu_marked=environ.get('COLAB_GPU') not in (None, '', '0'),
                 nvidia_node_indication=bool(nodes), hardware_model_verified=False, device_api_queries=0)
    if not (value['colab_gpu_marked'] or value['nvidia_node_indication']):
        raise ValueError('GPU-host indication not observed; do not create from CPU mode')
    return value


def executable_binding(entry, *, expected_resolved=None):
    resolved = entry.resolve(strict=True)
    if (not entry.is_file() or not os.access(entry, os.X_OK) or not resolved.is_relative_to(Path('/usr/bin'))
            or (expected_resolved is not None and resolved != expected_resolved)):
        raise ValueError('explicit lexical entry/resolved base executable mismatch')
    s = resolved.stat(); raw = read_regular(resolved, 16 * 1024**2)
    return dict(lexical=str(entry), resolved=str(resolved), is_symlink=entry.is_symlink(),
                device=s.st_dev, inode=s.st_ino, bytes=len(raw), sha256=digest(raw))


def child_environment(attempt):
    # Allowlist only: no inherited credentials/PIP/UV/PYTHONPATH/LD_* or user HOME.
    return dict(PATH='/usr/bin:/bin', LANG='C.UTF-8', HOME=str(attempt / 'home'), TMPDIR=str(attempt / 'tmp'),
        XDG_CACHE_HOME=str(attempt / 'cache'), XDG_CONFIG_HOME=str(attempt / 'config'),
        CUDA_VISIBLE_DEVICES='', NVIDIA_VISIBLE_DEVICES='', PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1',
        OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')


COLLECTOR = r'''
import ast,hashlib,importlib.metadata,json,os,platform,struct,sys,sysconfig
from importlib.machinery import PathFinder
from pathlib import Path
v=Path('/content/KLTN_GPU08_20261108_01/.venv')
assert sys.flags.isolated==1 and sys.flags.no_site==1 and sys.dont_write_bytecode
assert sys.executable==str(v/'bin/python')
assert os.environ.get('CUDA_VISIBLE_DEVICES')==os.environ.get('NVIDIA_VISIBLE_DEVICES')==''
assert 'venv' in sysconfig.get_scheme_names()
paths={k:Path(sysconfig.get_path(k,scheme='venv',vars={'base':str(v),'platbase':str(v)})) for k in ('purelib','platlib')}
assert all(p.is_dir() and p.resolve().is_relative_to(v) for p in paths.values())
assert all(not list(p.iterdir()) for p in set(paths.values()))
assert not list(importlib.metadata.distributions(path=[str(p) for p in set(paths.values())]))
specs={n:PathFinder.find_spec(n,[str(p) for p in set(paths.values())]) for n in ('pip','numpy','torch')}
assert all(s is None for s in specs.values())
assert not any(n in sys.modules for n in ('torch','numpy','pip','sitecustomize','usercustomize'))
version=f'{sys.version_info.major}.{sys.version_info.minor}'
base_dirs=[Path(f'{root}/lib/python{version}/{leaf}') for root in ('/usr','/usr/local') for leaf in ('site-packages','dist-packages')]
stdlib=[Path(p) for p in sys.path if p and ('site-packages' not in p and 'dist-packages' not in p)]
startup_allowed=[v,Path(f'/usr/lib/python{version}'),Path(f'/usr/local/lib/python{version}')]
empty_system=Path(f'/etc/python{version}/sitecustomize.py')
total=0
def fact(p):
 global total
 resolved=p.resolve()
 row={'path':str(p),'is_symlink':p.is_symlink(),'resolved_path':str(resolved),'approved_for_execution':False}
 if not(any(resolved.is_relative_to(x) for x in startup_allowed) or resolved==empty_system):
  return {**row,'status':'OUTSIDE_ALLOWED_STARTUP_ORIGIN_NOT_READ'}
 assert resolved.is_file() and not resolved.is_symlink()
 with resolved.open('rb') as f:body=f.read(65537)
 total+=len(body);assert len(body)<=65536 and total<=262144
 return {**row,'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest(),'status':'OBSERVED_NOT_EXECUTED_NOT_APPROVED'}
facts={}
for role,search in [('base',stdlib+base_dirs),('target',stdlib+list(paths.values()))]:
 pth=sorted({p for directory in search if directory.is_dir() for p in directory.glob('*.pth')})
 assert len(pth)<=64
 hooks=[];unknown=[]
 for name in ('sitecustomize','usercustomize'):
  spec=PathFinder.find_spec(name,[str(p) for p in search])
  if spec is not None:
   if spec.origin in (None,'built-in','frozen'):
    unknown.append({'module':name,'origin':spec.origin,'status':'UNKNOWN_CUSTOMIZE_ORIGIN_NOT_APPROVED','approved_for_execution':False})
   else:hooks.append(Path(spec.origin))
 facts[role]={'pth':[fact(p) for p in pth],'customize':[fact(p) for p in sorted(set(hooks))],'unknown_customize':unknown}
pip_spec=PathFinder.find_spec('pip',[str(p) for p in base_dirs])
pip_static=None
if pip_spec is not None and pip_spec.origin:
 p=Path(pip_spec.origin);row=fact(p);version_value=None
 if row.get('status')=='OBSERVED_NOT_EXECUTED_NOT_APPROVED':
  with p.resolve().open('rb') as f:body=f.read(65537)
  assert len(body)<=65536
  for node in ast.walk(ast.parse(body)):
   if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='__version__' for t in node.targets):
    if isinstance(node.value,ast.Constant) and type(node.value.value) is str:version_value=node.value.value
 pip_static={'origin':row,'version_from_static_ast':version_value,'runtime_probed':False}
result={'status':'EMPTY_VENV_NO_SITE_FACTS_ONLY','executable':sys.executable,'prefix_observed_no_site':sys.prefix,
 'base_prefix':sys.base_prefix,'python_version':platform.python_version(),'cache_tag':sys.implementation.cache_tag,
 'soabi':sysconfig.get_config_var('SOABI'),'extension_suffix':sysconfig.get_config_var('EXT_SUFFIX'),
 'gil_disabled':bool(sysconfig.get_config_var('Py_GIL_DISABLED')),'pointer_bits':struct.calcsize('P')*8,
 'machine':platform.machine(),'libc':platform.libc_ver(),'scheme':'venv','scheme_paths':{k:str(p) for k,p in paths.items()},
 'purelib_empty':True,'distributions':[],'target_package_specs':{n:None for n in specs},'startup_facts':facts,
 'base_pip_static_candidate':pip_static,'pip_runtime_version':None,'effective_pip_config':None,'target_tags':None,
 'normal_startup_executed':False,'normal_prefix_proven':False,'gpu_device_queries':0,'packages_installed':0}
print(json.dumps(result,allow_nan=False))
'''


def write_json(path, value):
    raw = json.dumps(value, indent=2, allow_nan=False).encode() + b'\n'
    if len(raw) > 128 * 1024: raise ValueError('bounded JSON output')
    with path.open('xb') as stream: stream.write(raw)


def cleanup_once(process, entry):
    if entry.get('cleanup_attempted'): return entry.get('cleanup_accepted', False)
    entry['cleanup_attempted'] = True; entry['signals'] = []; ok = True
    pgid = entry['pgid']
    if pgid <= 1 or pgid == os.getpgrp():
        entry['cleanup_accepted'] = False; return False
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try: os.killpg(pgid, sig); entry['signals'].append(dict(signal=int(sig), sent=True))
        except ProcessLookupError: entry['signals'].append(dict(signal=int(sig), absent=True))
        except OSError as error: ok = False; entry['signals'].append(dict(signal=int(sig), error=str(error)))
    try: process.wait(timeout=5)
    except (subprocess.TimeoutExpired, OSError) as error:
        ok = False; entry['reap_failed'] = True; entry['reap_error'] = str(error)
    entry['returncode'] = process.poll(); entry['cleanup_accepted'] = ok and entry['returncode'] is not None
    return entry['cleanup_accepted']


def resource_check(started, wall):
    elapsed = time.monotonic() - started; wall_elapsed = time.time() - wall
    if not all(math.isfinite(x) and 0 <= x <= CAP_SECONDS for x in (elapsed, wall_elapsed)):
        raise TimeoutError('30s total including cleanup/postelapsed exceeded')
    if (ATTEMPT / 'CANCEL').exists(): raise RuntimeError('owned cancellation requested')
    size = files = 0
    for root in (ROOT, ATTEMPT):
        if not root.exists(): continue
        for directory, _, names in os.walk(root, followlinks=False):
            for name in names:
                s = os.lstat(Path(directory) / name); size += max(s.st_size, getattr(s, 'st_blocks', 0) * 512); files += 1
                if size > CAP_BYTES or files > 4096: raise OSError('cooperative128MiB/file-count bound')
    if shutil.disk_usage(ROOT.parent).free < FLOOR_FREE: raise OSError('minimum30GiB free disk')
    if sum(p.stat().st_size for p in ATTEMPT.glob('*.stdout')) + sum(p.stat().st_size for p in ATTEMPT.glob('*.stderr')) > CAP_LOGS:
        raise OSError('combined4MiB log cap')
    return dict(elapsed_seconds=elapsed, wall_seconds=wall_elapsed, workspace_bytes=size)


def _owned_child(args):
    # Only outer Popen creates a session; all these descendants inherit this PGID.
    if os.getppid() != args.controller_pid or os.getpgrp() != os.getpid():
        raise ValueError('owned fresh session leader required')
    absent_root(ROOT)
    source = read_regular(Path(__file__), 128 * 1024); packet_raw = read_regular(STAGING / 'profile-packet.json', 16384)
    if digest(source) != args.expected_source_sha256 or digest(packet_raw) != args.profile_packet_sha256:
        raise ValueError('child source/packet drift')
    packet = validate_packet(json.loads(packet_raw)); before = abi_facts(); validate_abi(before, packet)
    base = executable_binding(BASE); ROOT.mkdir(mode=0o700, exist_ok=False)
    commands = []
    def run(name, command, timeout):
        began = time.monotonic()
        row = dict(name=name, command=command, returncode=None,
                   inherited_owned_pgid=os.getpgrp(), independent_session_created=False)
        commands.append(row)
        try:
            with (ATTEMPT / (name + '.stdout')).open('xb') as out, (ATTEMPT / (name + '.stderr')).open('xb') as err:
                p = subprocess.run(command, cwd=ATTEMPT, env=child_environment(ATTEMPT), stdout=out, stderr=err, timeout=timeout)
            row['returncode'] = p.returncode
            if p.returncode != 0: raise RuntimeError(name + ' failed; logs retained')
        except Exception as error:
            row.update(error_type=type(error).__name__, error=str(error)); raise
        finally:
            row['elapsed_seconds'] = time.monotonic() - began
            write_json(ATTEMPT / (name + '-receipt.json'), row)
    run('venv-create', [str(BASE), '-I', '-S', '-B', '-m', 'venv', '--without-pip', str(VENV)], 15)
    cfg = read_regular(VENV / 'pyvenv.cfg', 4096)
    validate_cfg(cfg)
    target_binding = executable_binding(VENV / 'bin/python', expected_resolved=Path(base['resolved']))
    with (ATTEMPT / 'target_probe.py').open('x', encoding='utf-8') as stream: stream.write(COLLECTOR)
    run('target-probe', [str(VENV / 'bin/python'), '-I', '-S', '-B', str(ATTEMPT / 'target_probe.py')], 5)
    facts = json.loads(read_regular(ATTEMPT / 'target-probe.stdout', 128 * 1024))
    if facts['python_version'] != before['python_version'] or facts['soabi'] != before['soabi']:
        raise ValueError('new target/current base ABI drift')
    with (ATTEMPT / 'pyvenv.cfg.snapshot').open('xb') as stream: stream.write(cfg)
    write_json(ATTEMPT / 'venv-descriptor.json', dict(schema_version=1, mode=MODE, status=PENDING,
        creation=dict(root_absent_before=True, root_created=True, venv_created_without_pip=True),
        source_sha256=args.expected_source_sha256, packet_sha256=args.profile_packet_sha256,
        actual_base_abi_before_creation=before, base_executable=base, target_executable=target_binding,
        pyvenv_cfg_sha256=digest(cfg), actual_target_facts=facts, commands=commands,
        packages_installed=0, gpu_device_queries=0, normal_startup_executed=False))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=(MODE,), required=True)
    parser.add_argument('--expected-source-sha256', required=True); parser.add_argument('--profile-packet-sha256', required=True)
    parser.add_argument('--approval-reference', required=True)
    parser.add_argument('--owned-child', action='store_true'); parser.add_argument('--controller-pid', type=int)
    args = parser.parse_args(argv)
    if not is_sha(args.expected_source_sha256) or not is_sha(args.profile_packet_sha256) or not args.approval_reference.strip():
        raise ValueError('explicit exact source/packet SHA and approval reference required')
    if os.name != 'posix' or platform.system() != 'Linux' or not sys.flags.no_site or not sys.flags.isolated or not sys.dont_write_bytecode:
        raise ValueError('Linux BASE -I -S -B only; no normal startup')
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '' or os.environ.get('NVIDIA_VISIBLE_DEVICES') != '':
        raise ValueError('both visibility variables must explicitly hide devices before bootstrap')
    if Path(sys.executable) != BASE or STAGING.resolve() != STAGING or STAGING.is_symlink() or STAGING.stat().st_uid != os.getuid():
        raise ValueError('fixed owned staging/current lexical base required')
    source_path = Path(__file__).absolute()
    if source_path != STAGING / 'gpu10_cold_bootstrap02.py': raise ValueError('source must be staged outside ROOT')
    source = read_regular(source_path, 128 * 1024); packet_raw = read_regular(STAGING / 'profile-packet.json', 16384)
    if digest(source) != args.expected_source_sha256 or digest(packet_raw) != args.profile_packet_sha256:
        raise ValueError('source/packet SHA mismatch before mutation')
    packet = validate_packet(json.loads(packet_raw))
    if args.owned_child:
        _owned_child(args); return 0
    ATTEMPT.mkdir(mode=0o700, exist_ok=False)
    start = time.monotonic(); wall = time.time(); process = None; entry = {}; result = dict(status='FAILED_RETAIN_PARTIAL_NO_RETRY', mode=MODE)
    try:
        absent_root(ROOT); before = abi_facts(); validate_abi(before, packet)
        indication = host_indication(os.environ, tuple(Path('/dev').glob('nvidia[0-9]*')))
        resource_check(start, wall)
        for name in ('home', 'tmp', 'cache', 'config'): (ATTEMPT / name).mkdir()
        with (ATTEMPT / 'source.py.snapshot').open('xb') as stream: stream.write(source)
        with (ATTEMPT / 'profile-packet.json.snapshot').open('xb') as stream: stream.write(packet_raw)
        write_json(ATTEMPT / 'preflight.json', dict(root_absent_before=True, actual_abi=before, gpu_host_indication=indication,
            source_sha256=args.expected_source_sha256, packet_sha256=args.profile_packet_sha256))
        command = [str(BASE), '-I', '-S', '-B', str(source_path), '--mode', MODE,
            '--expected-source-sha256', args.expected_source_sha256, '--profile-packet-sha256', args.profile_packet_sha256,
            '--approval-reference', args.approval_reference, '--owned-child', '--controller-pid', str(os.getpid())]
        with (ATTEMPT / 'child.stdout').open('xb') as out, (ATTEMPT / 'child.stderr').open('xb') as err:
            child_time_remaining(start, time.monotonic())
            process = subprocess.Popen(command, cwd=STAGING, env=child_environment(ATTEMPT), stdout=out, stderr=err, start_new_session=True)
            entry = dict(pid=process.pid, pgid=process.pid, command=command)
            try:
                while process.poll() is None:
                    child_time_remaining(start, time.monotonic())
                    resource_check(start, wall)
                    remaining = child_time_remaining(start, time.monotonic())
                    try: process.wait(timeout=min(.2, remaining))
                    except subprocess.TimeoutExpired: pass
                child_time_remaining(start, time.monotonic())  # Late RC0 cannot consume the cleanup reserve.
            finally:
                cleanup_once(process, entry)  # Immediate before child JSON parsing; never historical re-signal.
        if not entry.get('cleanup_accepted') or entry['returncode'] != 0: raise RuntimeError('child/cleanup failed')
        facts = json.loads(read_regular(ATTEMPT / 'venv-descriptor.json', 128 * 1024))
        if (facts['status'] != PENDING or facts['mode'] != MODE or not facts['creation']['root_absent_before']
                or facts['source_sha256'] != args.expected_source_sha256 or facts['packet_sha256'] != args.profile_packet_sha256):
            raise ValueError('fresh actual source/packet-bound creation receipt required')
        if read_regular(source_path, 128 * 1024) != source or read_regular(STAGING / 'profile-packet.json', 16384) != packet_raw:
            raise ValueError('source/packet changed')
        if digest(read_regular(VENV / 'pyvenv.cfg', 4096)) != facts['pyvenv_cfg_sha256']: raise ValueError('actual cfg changed')
        resource_check(start, wall)
        result.update(status=PENDING, descriptor_sha256=digest(read_regular(ATTEMPT / 'venv-descriptor.json', 128 * 1024)),
                      source_packet_prepost_equal=True, gpu_host_indication=indication)
    except Exception as error:
        result.update(error_type=type(error).__name__, error=str(error))
        with (ATTEMPT / 'failure.log').open('x', encoding='utf-8') as stream: stream.write(traceback.format_exc())
    finally:
        if process is not None and not entry.get('cleanup_attempted'): cleanup_once(process, entry)
        # Hash all bounded outputs before the operative elapsed verdict, including failures.
        outputs = {}
        try:
            for p in ATTEMPT.iterdir():
                if p.is_file() and p.name not in {'result.json', 'output-manifest.json'}:
                    raw = read_regular(p, CAP_LOGS)
                    outputs[p.name] = dict(bytes=len(raw), sha256=digest(raw))
            resource_check(start, wall)
        except Exception as error:
            result.update(status='REJECTED_RESOURCE_BOUND_RETAIN_PARTIAL',
                          output_hash_or_resource_error_type=type(error).__name__, output_hash_or_resource_error=str(error))
        elapsed = time.monotonic() - start; wall_elapsed = time.time() - wall
        cleanup_ok = process is None or entry.get('cleanup_accepted') is True
        time_ok = all(math.isfinite(x) and 0 <= x <= CAP_SECONDS for x in (elapsed, wall_elapsed))
        if not cleanup_ok: result['status'] = 'CLEANUP_UNVERIFIED_RETAIN_PARTIAL'
        if not time_ok: result['status'] = 'REJECTED_RESOURCE_BOUND_RETAIN_PARTIAL'
        result.update(elapsed_seconds=elapsed, elapsed_wall_seconds=wall_elapsed, timeout_seconds=30,
            cleanup=entry, cleanup_accepted=cleanup_ok, resource_time_accepted=time_ok, storage_bound_is_cooperative=True,
            approval_reference=args.approval_reference, packages_installed=0, pip_executed=False, normal_startup_executed=False,
            gpu_device_queries=0, model_optimizer_steps=0, retry_count=0, installer_authorized=False)
        write_json(ATTEMPT / 'result.json', result)
        final_raw = read_regular(ATTEMPT / 'result.json', 128 * 1024)
        outputs['result.json'] = dict(bytes=len(final_raw), sha256=digest(final_raw))
        write_json(ATTEMPT / 'output-manifest.json', dict(status=result['status'], outputs=outputs,
            excludes='Created .venv and owned home/tmp/cache/config directories; no binary/credential export'))
        print(json.dumps(dict(status=result['status'], result_sha256=digest(read_regular(ATTEMPT / 'result.json', 128 * 1024)),
                             output_manifest_sha256=digest(read_regular(ATTEMPT / 'output-manifest.json', 128 * 1024)))))
    return 0 if result['status'] == PENDING else 1


if __name__ == '__main__':
    raise SystemExit(main())
