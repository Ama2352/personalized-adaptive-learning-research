"""Pure cold-install prerequisite checks; no launcher or runtime authority.

Inputs are byte copies plus an independently reviewed pin map. This module does
not read a filesystem, discover a host, authenticate a receipt, or install. A
caller must obtain/approve fresh facts separately. Public packaging supplies all
wheel/PEP440/PEP508 semantics; no dependency resolution is performed.
"""
import hashlib
import json
import math
import re
from urllib.parse import unquote, urlsplit

import packaging
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.tags import parse_tag
from packaging.utils import canonicalize_name, parse_wheel_filename
from packaging.version import Version

ROOT = '/content/KLTN_GPU08_20261108_01'
VENV = ROOT + '/.venv'
BOOT_SOURCE = '037d5aafc1490afb0ae36c0abb216552625a52993f2dfffee1aa4d6d1a5c5883'
BOOT_POLICY = '5a0845d46156c06a8d284350e1b63b93af1649badddc8dae787e74e584002898'
LOCK_SHA = '60dad3de310562db4f775d1977e2097a6d1c8f57a22bfa4f7afc3ceab35cc45a'
REPORT_SHA = '92a2bbae1cdf285491bac1d67082d16c824aeb2ca9447d841a8182807be671dd'
RESOLUTION_SHA = '32fe949645d44a84e236c5a579be6312cd8c72e19ebd2e8c3c35de0aee216397'
PENDING = 'FRESH_EMPTY_VENV_DISCOVERY_PENDING_STARTUP_AND_PIP_REVIEW'
MODE = 'GPU_HOST_CUDA_HIDDEN_INSTALL_EMPTY'
LABELS = ('fresh_bootstrap_descriptor', 'bootstrap_result', 'bootstrap_policy',
          'actual_cfg', 'fresh_empty_probe', 'startup_review', 'base_pip_review',
          'linux_lock', 'selected_report', 'resolution_provenance', 'target_compatibility')
FRESH_LABELS = ('fresh_empty_probe', 'startup_review', 'base_pip_review', 'target_compatibility')
MARKER_FIELDS = frozenset(('implementation_name', 'implementation_version', 'os_name',
    'platform_machine', 'platform_release', 'platform_system', 'platform_version',
    'python_full_version', 'platform_python_implementation', 'python_version', 'sys_platform'))
POLICY = dict(packages=44, nvidia_packages=14, overall_seconds=600, install_deadline_seconds=480,
              workspace_bytes=20 * 1024**3, minimum_free_bytes=30 * 1024**3,
              visible_devices_during_install='CUDA_AND_NVIDIA_HIDDEN', attempts=1,
              requested_root_extras=[])


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(raw):
    require(type(raw) is bytes, 'byte input required')
    return hashlib.sha256(raw).hexdigest()


def exact_keys(value, keys, reason):
    require(type(value) is dict and set(value) == set(keys), reason)


def text(value):
    require(type(value) is str and bool(value.strip()), 'nonempty text required')
    return value


def hash_value(value):
    require(type(value) is str and re.fullmatch('[a-f0-9]{64}', value) is not None, 'strict SHA256 required')
    return value


def number(value, maximum):
    require(type(value) in (int, float) and math.isfinite(value) and 0 <= value <= maximum,
            'bounded finite non-bool number required')


def same(actual, expected, reason):
    require(type(actual) is type(expected), reason)
    if type(expected) is dict:
        require(set(actual) == set(expected), reason)
        for key in expected: same(actual[key], expected[key], reason)
    elif type(expected) is list:
        require(len(actual) == len(expected), reason)
        for left, right in zip(actual, expected): same(left, right, reason)
    else:
        require(actual == expected, reason)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def decode(raw):
    require(type(raw) is bytes and len(raw) <= 8 * 1024**2, 'bounded byte JSON required')
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'duplicate JSON key')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs,
        parse_constant=lambda value: (_ for _ in ()).throw(ValueError('nonfinite JSON')))


def validate_cfg(raw):
    require(type(raw) is bytes and len(raw) <= 4096, 'bounded actual cfg bytes')
    values = {}
    for line in raw.decode('utf-8').splitlines():
        if not line.strip():
            continue
        require('=' in line, 'invalid cfg row')
        key, value = (p.strip() for p in line.split('=', 1))
        key = key.lower()
        require(key not in values, 'duplicate cfg key')
        values[key] = value
    same(values.get('include-system-site-packages', '').lower(), 'false', 'system site packages disabled')
    same(values.get('home'), '/usr/bin', 'actual base home required')
    return values


def validate_abi(abi):
    require(type(abi) is dict, 'actual ABI object required')
    for key, value in dict(implementation='cpython', system='Linux', machine='x86_64',
                          pointer_bits=64, gil_disabled=False, isolated=1, no_site=1,
                          bytecode_disabled=True, executable='/usr/bin/python3').items():
        same(abi.get(key), value, 'actual no-site base ABI: ' + key)
    version = Version(text(abi.get('python_version')))
    require(len(version.release) == 3, 'full Python patch version required')
    same(abi.get('cache_tag'), f'cpython-{version.major}{version.minor}', 'cache tag ABI mismatch')
    for key in ('soabi', 'extension_suffix', 'prefix', 'base_prefix', 'python_full'):
        text(abi.get(key))
    require(abi['soabi'].startswith(f'cpython-{version.major}{version.minor}-'), 'SOABI mismatch')
    require(abi['extension_suffix'] == '.' + abi['soabi'] + '.so', 'extension suffix mismatch')
    require(type(abi.get('libc')) is list and len(abi['libc']) == 2 and abi['libc'][0] == 'glibc', 'actual glibc tuple')
    Version(text(abi['libc'][1]))
    return abi


def executable(row, lexical):
    require(type(row) is dict, 'executable fact required')
    same(row.get('lexical'), lexical, 'lexical executable entry mismatch')
    resolved = text(row.get('resolved'))
    require(re.fullmatch(r'/usr/bin/python3(?:\.\d+)?', resolved) is not None, 'resolved current base entry')
    require(type(row.get('is_symlink')) is bool, 'actual symlink fact')
    for key in ('device', 'inode', 'bytes'):
        require(type(row.get(key)) is int and row[key] > 0, 'executable stat fact')
    hash_value(row.get('sha256'))


def trusted_inputs(packet, blobs, review):
    exact_keys(review, ('role', 'parent_review_reference', 'run_id', 'artifact_sha256',
                       'producer_sha256', 'evaluator_packaging_version', 'bootstrap_approval_reference'), 'strict external review object')
    require(review['role'] in ('ENGINEERING_FIXTURE', 'REVIEWED_ACTUAL_FRESH_GPU_HOST'), 'external review role')
    text(review['parent_review_reference'])
    text(review['bootstrap_approval_reference'])
    same(packet.get('parent_review_reference'), review['parent_review_reference'], 'approval binding')
    same(packet.get('run_id'), review['run_id'], 'fresh attempt binding')
    same(review['evaluator_packaging_version'], packaging.__version__, 'review actual evaluator packaging version')
    exact_keys(blobs, LABELS, 'all11 byte copies required')
    exact_keys(review['artifact_sha256'], LABELS, 'external pins for all11 artifacts')
    exact_keys(review['producer_sha256'], FRESH_LABELS, 'reviewed producer sources required')
    for key in FRESH_LABELS:
        hash_value(review['producer_sha256'][key])
    exact_keys(packet, ('schema_version', 'role', 'mode', 'run_id', 'target_root',
                       'parent_review_reference', 'artifacts', 'policy'), 'strict packet fields')
    for key, expected in dict(schema_version=1, role='COLD_INSTALL_PREREQUISITES_NOT_EXECUTION_AUTHORITY',
                             mode=MODE, target_root=ROOT).items():
        same(packet[key], expected, 'packet constant: ' + key)
    require(re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,47}', packet['run_id']) is not None, 'attempt identifier')
    exact_keys(packet['policy'], POLICY, 'policy keys')
    for key, expected in POLICY.items():
        same(packet['policy'][key], expected, 'fixed policy: ' + key)
    exact_keys(packet['artifacts'], LABELS, 'strict11 artifacts')
    paths = set()
    for label in LABELS:
        row = packet['artifacts'][label]
        exact_keys(row, ('root_relative_copy', 'original_locator', 'origin_kind', 'bytes',
                         'sha256_before_copy', 'sha256_after_copy'), 'artifact fields')
        path = row['root_relative_copy']
        require(type(path) is str and re.fullmatch(r'artifacts/akt/gpu10-cold-install-inputs/[A-Za-z0-9_-]+/[A-Za-z0-9_.-]+', path)
                and path.split('/')[-1] not in ('.', '..') and path not in paths, 'unique lexical copied path')
        paths.add(path)
        text(row['original_locator'])
        expected_origin = ('HISTORICAL_LINUX_RESOLVER_METADATA' if label in
            ('linux_lock', 'selected_report', 'resolution_provenance') else
            'REVIEWED_POLICY_INPUT' if label == 'bootstrap_policy' else
            'LOCAL_DERIVED_RECEIPT_FROM_VERIFIED_RPC' if label in ('startup_review', 'base_pip_review', 'target_compatibility')
            else 'REMOTE_ACTUAL_STAGE_ARTIFACT')
        same(row['origin_kind'], expected_origin, 'artifact original provenance: ' + label)
        require(type(blobs[label]) is bytes and len(blobs[label]) <= 8 * 1024**2, 'bounded bytes')
        same(row['bytes'], len(blobs[label]), 'copied byte size')
        actual = sha(blobs[label])
        for value in (row['sha256_before_copy'], row['sha256_after_copy'], review['artifact_sha256'][label]):
            same(hash_value(value), actual, 'copied byte/external pin mismatch: ' + label)
    for label, pin in dict(bootstrap_policy=BOOT_POLICY, linux_lock=LOCK_SHA,
                           selected_report=REPORT_SHA, resolution_provenance=RESOLUTION_SHA).items():
        same(sha(blobs[label]), pin, 'frozen source metadata pin: ' + label)


def common_receipt(row, label, packet, blobs, review, abi_sha):
    exact_keys(row, ('schema_version', 'role', 'status', 'run_id', 'approval_reference',
        'source_sha256', 'bindings', 'facts'), 'strict future receipt contract: ' + label)
    same(row['schema_version'], 1, 'receipt schema')
    same(row['role'], 'FRESH_GPU_HOST_' + label.upper(), 'fresh GPU-host role required')
    same(row['status'], 'REVIEWED_PASS', 'receipt must be reviewed, not pending')
    same(row['run_id'], packet['run_id'], 'fresh receipt attempt')
    same(row['approval_reference'], review['parent_review_reference'], 'fresh review reference')
    same(row['source_sha256'], review['producer_sha256'][label], 'reviewed source identity')
    expected = dict(descriptor_sha256=sha(blobs['fresh_bootstrap_descriptor']),
        bootstrap_result_sha256=sha(blobs['bootstrap_result']), cfg_sha256=sha(blobs['actual_cfg']),
        abi_sha256=abi_sha)
    same(row['bindings'], expected, 'fresh descriptor/cfg/ABI/result bindings')
    require(type(row['facts']) is dict, 'receipt facts object')
    return row['facts']


def evaluate_compatibility(report, lock_bytes, target, *, expected_bindings):
    """Fixed44 consistency only. Never substitutes local/CPU default markers."""
    exact_keys(target, ('marker_environment', 'tags', 'requested_root_extras', 'bindings'), 'compatibility facts keys')
    same(target['bindings'], expected_bindings, 'compatibility evidence bindings')
    env = target['marker_environment']
    exact_keys(env, MARKER_FIELDS, 'all11 actual target PEP508 fields required')
    for value in env.values(): text(value)
    same(env['implementation_name'], 'cpython', 'target implementation')
    same(env['platform_python_implementation'], 'CPython', 'target implementation label')
    for key, expected in dict(sys_platform='linux', os_name='posix', platform_system='Linux', platform_machine='x86_64').items():
        same(env[key], expected, 'target marker OS: ' + key)
    version = Version(env['python_full_version'])
    same(env['python_version'], f'{version.major}.{version.minor}', 'marker Python minor')
    same(env['implementation_version'], env['python_full_version'], 'CPython implementation version')
    same(target['requested_root_extras'], [], 'no adopted root extras')
    require(type(target['tags']) is list and 0 < len(target['tags']) <= 10000
            and len(target['tags']) == len(set(target['tags'])), 'bounded unique actual tags')
    tags = set()
    for tag in target['tags']:
        text(tag)
        parsed = parse_tag(tag)
        require(len(parsed) == 1, 'actual supported tags must be uncompressed triples')
        tags.update(parsed)
    require(type(lock_bytes) is bytes and len(lock_bytes) <= 128 * 1024, 'bounded lock bytes')
    locked = {}
    for line in lock_bytes.decode('utf-8').splitlines():
        match = re.fullmatch(r'([A-Za-z0-9_.-]+) @ (https://\S+) --hash=sha256:([a-f0-9]{64})', line)
        require(match is not None, 'exact direct-wheel hash lock row')
        name, url, digest = match.groups(); name = canonicalize_name(name)
        require(name not in locked, 'duplicate lock package')
        parts = urlsplit(url)
        require(parts.hostname in ('files.pythonhosted.org', 'download.pytorch.org', 'download-r2.pytorch.org') and
                parts.netloc == parts.hostname and not parts.query and not parts.fragment, 'official exact wheel URL')
        filename = unquote(parts.path.rsplit('/', 1)[-1])
        require('/' not in filename and '\\' not in filename, 'wheel basename')
        wheel_name, wheel_version, _, wheel_tags = parse_wheel_filename(filename)
        same(str(wheel_name), name, 'wheel distribution name mismatch')
        require(bool(tags.intersection(wheel_tags)), 'wheel unsupported by actual target tags: ' + name)
        locked[name] = dict(url=url, sha256=digest, version=wheel_version, tags=wheel_tags)
    require(len(locked) == 44, 'exact44 lock closure')
    require(type(report) is dict and type(report.get('install')) is list and len(report['install']) == 44, 'selected44 report')
    selected = {}; wheels = []; root_count = 0
    for item in report['install']:
        require(type(item) is dict and type(item.get('metadata')) is dict, 'selected metadata')
        md = item['metadata']; name = str(canonicalize_name(text(md.get('name'))))
        require(name not in selected and name in locked, 'unique selected distribution')
        ver = Version(text(md.get('version'))); same(ver, locked[name]['version'], 'wheel/report version mismatch')
        download = item.get('download_info', {})
        same(download.get('url'), locked[name]['url'], 'report/lock URL mismatch')
        same(download.get('archive_info', {}).get('hashes', {}).get('sha256'), locked[name]['sha256'], 'report/lock wheel hash')
        require(type(item.get('requested')) is bool, 'actual requested-root flag')
        root_count += int(item['requested'])
        require(item.get('requested_extras', []) == [], 'requested extras not supported without review')
        py = md.get('requires_python')
        if py is not None:
            text(py); require(SpecifierSet(py).contains(version, prereleases=True), 'Requires-Python unsatisfied: ' + name)
        reqs = md.get('requires_dist', [])
        require(type(reqs) is list and len(reqs) <= 1024 and all(type(r) is str for r in reqs), 'raw Requires-Dist rows')
        selected[name] = (ver, reqs)
        wheels.append(dict(name=name, version=str(ver), requires_python=py,
            python_status='unspecified' if py is None else 'satisfied', tag_supported=True))
    require(set(selected) == set(locked) and root_count == 29, 'exact44 distributions/29 requested roots')
    require(sum(n.startswith('nvidia-') for n in selected) == 14, 'exact14 NVIDIA distributions')
    rows = []
    for owner, (_, reqs) in selected.items():
        for index, raw in enumerate(reqs):
            req = Requirement(raw)
            # Public Marker only; explicit empty extra plus COMPLETE target fields avoids local fallback.
            active = req.marker is None or req.marker.evaluate(environment={**env, 'extra': ''})
            row = dict(owner=owner, index=index, raw=raw, active=active,
                       marker=str(req.marker) if req.marker is not None else None)
            if active:
                require(not req.url and not req.extras, 'active direct URL/extras require separate review')
                provider = str(canonicalize_name(req.name))
                require(provider in selected, 'active dependency missing: ' + provider)
                value = selected[provider][0]
                require(req.specifier.contains(value, prereleases=True), 'active dependency conflict: ' + provider)
                row.update(provider=provider, selected_version=str(value), status='satisfied')
            else:
                row['status'] = 'inactive_for_explicit_target_no_requested_extras'
            rows.append(row)
    return dict(status='FIXED44_METADATA_COMPATIBLE_NOT_WHEEL_BYTES_OR_INSTALL_PROOF',
        packaging_version=packaging.__version__, wheel_checks=wheels, dependency_rows=rows,
        packages=44, nvidia_packages=14, requested_roots=root_count,
        requires_python_declared=sum(w['requires_python'] is not None for w in wheels),
        requires_python_unspecified=sum(w['requires_python'] is None for w in wheels),
        requires_dist_rows=len(rows), active_requires_dist=sum(r['active'] for r in rows),
        inactive_requires_dist=sum(not r['active'] for r in rows), execution_authorized=False)


def validate_packet(packet, artifact_bytes, *, trusted_review):
    """Validate declared provenance/bindings. External trust and current facts stay caller responsibilities."""
    trusted_inputs(packet, artifact_bytes, trusted_review)
    data = {key: decode(raw) for key, raw in artifact_bytes.items() if key not in ('actual_cfg', 'linux_lock')}
    desc = data['fresh_bootstrap_descriptor']; result = data['bootstrap_result']
    same(desc.get('schema_version'), 1, 'descriptor schema')
    same(desc.get('mode'), 'GPU_HOST_CUDA_HIDDEN_BOOTSTRAP_EMPTY', 'old CPU descriptor rejected')
    same(desc.get('status'), PENDING, 'fresh cold02 descriptor required')
    same(desc.get('source_sha256'), BOOT_SOURCE, 'exact cold02 source')
    same(desc.get('packet_sha256'), BOOT_POLICY, 'exact bootstrap policy')
    same(desc.get('creation'), dict(root_absent_before=True, root_created=True, venv_created_without_pip=True), 'actual fresh creation')
    same(desc.get('pyvenv_cfg_sha256'), sha(artifact_bytes['actual_cfg']), 'actual cfg identity')
    validate_cfg(artifact_bytes['actual_cfg'])
    for key, value in dict(packages_installed=0, gpu_device_queries=0, normal_startup_executed=False).items():
        same(desc.get(key), value, 'bootstrap no-install/no-normal-startup facts')
    abi = validate_abi(desc.get('actual_base_abi_before_creation')); abi_sha = sha(canonical(abi))
    same(validate_cfg(artifact_bytes['actual_cfg']).get('version'), abi['python_version'], 'actual cfg/base ABI version')
    executable(desc.get('base_executable'), '/usr/bin/python3')
    executable(desc.get('target_executable'), VENV + '/bin/python')
    same(desc['base_executable']['resolved'], desc['target_executable']['resolved'], 'current base target executable binding')
    same(desc['base_executable']['sha256'], desc['target_executable']['sha256'], 'current base target bytes')
    facts = desc.get('actual_target_facts'); require(type(facts) is dict, 'actual cold no-site facts')
    for key in ('python_version', 'cache_tag', 'soabi', 'extension_suffix', 'gil_disabled', 'pointer_bits', 'machine', 'libc'):
        same(facts.get(key), abi[key], 'base/target ABI equality: ' + key)
    for key, value in dict(status='EMPTY_VENV_NO_SITE_FACTS_ONLY', executable=VENV + '/bin/python',
            purelib_empty=True, distributions=[], target_package_specs=dict(pip=None, numpy=None, torch=None),
            normal_startup_executed=False, normal_prefix_proven=False, packages_installed=0, gpu_device_queries=0,
            pip_runtime_version=None, effective_pip_config=None, target_tags=None, scheme='venv').items():
        same(facts.get(key), value, 'cold no-site emptiness: ' + key)
    same(result.get('status'), PENDING, 'actual bootstrap result accepted pending only')
    same(result.get('mode'), 'GPU_HOST_CUDA_HIDDEN_BOOTSTRAP_EMPTY', 'bootstrap result mode')
    same(result.get('descriptor_sha256'), sha(artifact_bytes['fresh_bootstrap_descriptor']), 'descriptor result binding')
    same(result.get('approval_reference'), trusted_review['bootstrap_approval_reference'], 'independent actual bootstrap approval binding')
    same(result.get('timeout_seconds'), 30, 'bootstrap cap identity')
    for key in ('cleanup_accepted', 'resource_time_accepted', 'source_packet_prepost_equal'):
        same(result.get(key), True, 'bootstrap resource/source/cleanup')
    require(type(result.get('cleanup')) is dict and result['cleanup'].get('cleanup_accepted') is True
            and type(result['cleanup'].get('returncode')) is int and result['cleanup']['returncode'] == 0, 'owned bootstrap child cleanup/RC0')
    number(result.get('elapsed_seconds'), 30); number(result.get('elapsed_wall_seconds'), 30)
    indication = result.get('gpu_host_indication', {})
    require(indication.get('colab_gpu_marked') is True or indication.get('nvidia_node_indication') is True, 'fresh GPU-host indication')
    same(result.get('installer_authorized'), False, 'bootstrap cannot authorize installer')
    for key, value in dict(pip_executed=False, normal_startup_executed=False, packages_installed=0,
                           gpu_device_queries=0, model_optimizer_steps=0, retry_count=0).items():
        same(result.get(key), value, 'bootstrap bounded no-execution ledger')
    normal = common_receipt(data['fresh_empty_probe'], 'fresh_empty_probe', packet, artifact_bytes, trusted_review, abi_sha)
    for key, value in dict(prefix=VENV, executable=VENV + '/bin/python', base_prefix=abi['base_prefix'],
            distributions=[], package_specs=dict(pip=None, numpy=None, torch=None), user_site_enabled=False,
            normal_startup=True, purelib_empty=True, cfg_sha256=sha(artifact_bytes['actual_cfg']), abi_sha256=abi_sha).items():
        same(normal.get(key), value, 'fresh normal empty-target fact: ' + key)
    startup = common_receipt(data['startup_review'], 'startup_review', packet, artifact_bytes, trusted_review, abi_sha)
    for key in ('base_approved', 'target_approved', 'unknown_hooks_absent', 'cuda_hidden', 'record_bindings_accepted'):
        same(startup.get(key), True, 'review both current startup chains')
    for key in ('base_facts_sha256', 'target_facts_sha256', 'review_manifest_sha256'):
        hash_value(startup.get(key))
    pip = common_receipt(data['base_pip_review'], 'base_pip_review', packet, artifact_bytes, trusted_review, abi_sha)
    for key, value in dict(version='26.2.2', python_isolated=True, config_file='/dev/null',
                           file_effective_entries=[], pip_env_names=['PIP_CONFIG_FILE']).items():
        same(pip.get(key), value, 'reviewed current basepip/config: ' + key)
    text(pip.get('origin')); hash_value(pip.get('origin_sha256'))
    effective = pip.get('effective_config')
    require(effective in ({':env:.config-file': '/dev/null'}, {':env:': {':env:.config-file': '/dev/null'}}), 'strict flat/nested devnull only')
    compat = common_receipt(data['target_compatibility'], 'target_compatibility', packet, artifact_bytes, trusted_review, abi_sha)
    env = compat.get('marker_environment', {})
    same(env.get('python_full_version'), abi['python_version'], 'target marker/actual ABI version')
    resolution = data['resolution_provenance']
    for key, value in dict(status='CANDIDATE_CLOSURE_RESOLVED_NOT_INSTALLED', packages_installed=0,
                           isolated_site_unchanged=True, returncode=0).items():
        same(resolution.get(key), value, 'historical metadata provenance only')
    bindings = dict(descriptor_sha256=sha(artifact_bytes['fresh_bootstrap_descriptor']),
        cfg_sha256=sha(artifact_bytes['actual_cfg']), startup_review_sha256=sha(artifact_bytes['startup_review']),
        base_pip_review_sha256=sha(artifact_bytes['base_pip_review']), empty_probe_sha256=sha(artifact_bytes['fresh_empty_probe']),
        lock_sha256=LOCK_SHA, selected_report_sha256=REPORT_SHA, abi_sha256=abi_sha)
    evaluation = evaluate_compatibility(data['selected_report'], artifact_bytes['linux_lock'], compat, expected_bindings=bindings)
    return dict(status=('ENGINEERING_PACKET_CONSISTENT_NOT_RUNTIME_FACTS' if trusted_review['role'] == 'ENGINEERING_FIXTURE'
                       else 'DECLARED_REVIEWED_PACKET_CONSISTENT_REQUIRES_CURRENT_HOST_RECHECK'),
        execution_authorized=False, runtime_or_install_verified=False, compatibility=evaluation,
        limitation='Pure byte/receipt consistency; no live origins, file bytes, freshness or external approval authentication.')
