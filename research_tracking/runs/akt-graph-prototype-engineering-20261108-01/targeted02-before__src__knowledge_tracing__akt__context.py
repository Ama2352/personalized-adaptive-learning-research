"""Context bất biến cho worker synthetic; không cấp quyền thực thi.

Sidecar được hash riêng, giữ nguyên serialization/config hash CPU lịch sử.
Chỉ nhận input nhỏ khai báo synthetic trong artifacts/akt; không mở Junyi/Test.
"""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import re

from .config import DataPaths, PROJECT_ROOT

MAX_CONTEXT_BYTES = 65536
MAX_INPUT_BYTES = 128 * 1024**2


def _digest(path, budget):
    h = hashlib.sha256()
    size = 0
    with path.open('rb') as stream:
        while True:
            chunk = stream.read(min(1024**2, budget-size+1))
            if not chunk:break
            size += len(chunk)
            if size>budget:raise ValueError('synthetic inputs exceed byte budget')
            h.update(chunk)
    return h.hexdigest(),size


@dataclass(frozen=True)
class CudaLimits:
    max_vram_bytes: int
    visible_devices: int


@dataclass(frozen=True)
class WorkerContext:
    manifest_path: Path
    manifest_sha256: str
    project_root: Path
    runtime_report: Path
    lock_file: Path
    gate2_report: Path
    dataset_root: Path
    data_paths: DataPaths
    input_hashes: tuple[tuple[str, str], ...]
    cuda_limits: CudaLimits | None

    @property
    def identity(self):
        result={'worker_context_schema': 1, 'worker_context_sha256': self.manifest_sha256,
                'worker_context_inputs_sha256': dict(self.input_hashes),
                'worker_context_scope': 'synthetic-development-only'}
        if self.cuda_limits is not None:
            result['worker_context_cuda_limits']={'max_vram_bytes':self.cuda_limits.max_vram_bytes,
                                                 'visible_devices':self.cuda_limits.visible_devices}
        return result

    def revalidate(self, project_root):
        if self.project_root != Path(project_root).resolve():
            raise ValueError('worker context project mismatch')
        current = load_worker_context(self.manifest_path, expected_sha256=self.manifest_sha256,
                                      project_root=project_root)
        if current != self:raise ValueError('worker context or inputs changed')
        return self

    def validate_for(self, config):
        if config.phase not in {'preflight','smoke','pilot','cuda-smoke'}:
            raise ValueError('worker context is unavailable for fold/full research execution')
        if (config.phase=='cuda-smoke') != (self.cuda_limits is not None):
            raise ValueError('CUDA smoke requires explicit CUDA limits; CPU contexts cannot claim CUDA budgets')
        return self.revalidate(config.project_root)


def load_worker_context(path: Path, *, expected_sha256: str, project_root: Path = PROJECT_ROOT) -> WorkerContext:
    root = Path(project_root).resolve()
    path = Path(path).resolve()
    allowed = ((root/'artifacts/akt').resolve(), (root/'experiments/akt/configs').resolve())
    if not any(path.is_relative_to(base) and path != base for base in allowed):
        raise ValueError('context sidecar outside approved AKT paths')
    if not isinstance(expected_sha256, str) or not re.fullmatch('[a-f0-9]{64}',expected_sha256):
        raise ValueError('context requires exact SHA-256')
    with path.open('rb') as stream:payload=stream.read(MAX_CONTEXT_BYTES+1)
    if len(payload)>MAX_CONTEXT_BYTES or hashlib.sha256(payload).hexdigest()!=expected_sha256:
        raise ValueError('context size or SHA-256 mismatch')
    value=json.loads(payload)
    keys={'schema_version','scope','runtime_report','lock_file','gate2_report','dataset_root',
          'canonical','assignments','canonical_manifest','split_manifest','input_hashes'}
    if (not isinstance(value,dict) or set(value) not in (keys,keys|{'cuda_limits'})
            or type(value['schema_version']) is not int or value['schema_version']!=1
            or value['scope']!='synthetic-development-only'):
        raise ValueError('invalid synthetic worker context schema/scope')
    limits=None
    if 'cuda_limits' in value:
        limit=value['cuda_limits']
        if (not isinstance(limit,dict) or set(limit)!={'max_vram_bytes','visible_devices'}
                or type(limit['max_vram_bytes']) is not int or not 64*1024**2<=limit['max_vram_bytes']<=2*1024**3
                or type(limit['visible_devices']) is not int or limit['visible_devices']!=1):
            raise ValueError('invalid bounded CUDA limits')
        limits=CudaLimits(limit['max_vram_bytes'],limit['visible_devices'])

    def resolve(name):
        text=value[name]
        if not isinstance(text,str) or not text or '\\' in text or ':' in text:
            raise ValueError('context paths must be project-relative POSIX paths')
        relative=PurePosixPath(text)
        if relative.is_absolute() or '..' in relative.parts or any(c in text for c in '*?[]'):
            raise ValueError('unsafe context path')
        target=(root/text).resolve()
        if not target.is_relative_to(root) or target==root:
            raise ValueError('context path escapes project')
        protected=(root/'dataset',root/'artifacts/bkt_baseline',root/'venv',root/'.wsl',root/'artifacts/akt/private')
        if any(target.is_relative_to(base.resolve()) for base in protected):
            raise ValueError('context cannot point to protected inputs')
        return target

    runtime,lock,gate=(resolve(n) for n in ('runtime_report','lock_file','gate2_report'))
    for target in (runtime,gate):
        if not target.is_relative_to((root/'artifacts/akt/preflight').resolve()):
            raise ValueError('runtime and Gate2 reports must be AKT preflight files')
    if not (lock.is_relative_to((root/'artifacts/akt').resolve())
            or (lock.parent==root and lock.name.startswith('requirements-akt') and lock.name.endswith('.txt'))):
        raise ValueError('invalid AKT runtime lock path')
    dataset=resolve('dataset_root')
    if not dataset.is_relative_to((root/'artifacts/akt').resolve()) or dataset==(root/'artifacts/akt').resolve():
        raise ValueError('synthetic dataset root must be inside artifacts/akt')
    paths=DataPaths(*(resolve(n) for n in ('canonical','assignments','canonical_manifest','split_manifest')))
    if any(not p.is_relative_to(dataset) or p==dataset for p in (paths.canonical,paths.assignments,paths.canonical_manifest,paths.split_manifest)):
        raise ValueError('synthetic inputs must share dataset root')
    marker=dataset/'SYNTHETIC_ONLY.json'
    inputs={marker,paths.assignments,paths.canonical_manifest,paths.split_manifest}
    if paths.canonical.is_dir():
        if any(p.is_symlink() or p.is_junction() for p in paths.canonical.rglob('*')):
            raise ValueError('synthetic canonical tree cannot contain symlinks')
        parquet=list(paths.canonical.rglob('*.parquet'))
    else:
        if paths.canonical.suffix!='.parquet':raise ValueError('canonical file must be Parquet')
        parquet=[paths.canonical]
    if not 1<=len(parquet)<=64:raise ValueError('synthetic Parquet inventory must have 1..64 files')
    for p in parquet:
        if not p.resolve().is_relative_to(dataset) or not p.is_file():
            raise ValueError('synthetic Parquet escapes dataset root')
        inputs.add(p.resolve())
    total=0
    for p in inputs:
        if not p.resolve().is_relative_to(dataset) or not p.is_file():raise ValueError('invalid synthetic input')
        total+=p.stat().st_size
    if total>MAX_INPUT_BYTES:raise ValueError('synthetic inputs exceed 128MiB budget')
    with marker.open('rb') as stream:marker_bytes=stream.read(MAX_CONTEXT_BYTES+1)
    if len(marker_bytes)>MAX_CONTEXT_BYTES:raise ValueError('synthetic marker too large')
    declared=json.loads(marker_bytes)
    if (not isinstance(declared,dict) or declared.get('synthetic_only') is not True
            or declared.get('real_data_authorized') is not False):
        raise ValueError('dataset is not declared synthetic-only')
    actual=0;records=[]
    for p in sorted(inputs):
        digest,size=_digest(p,MAX_INPUT_BYTES-actual)
        actual+=size
        if p==marker and digest!=hashlib.sha256(marker_bytes).hexdigest():
            raise ValueError('synthetic marker changed during inspection')
        records.append((p.relative_to(root).as_posix(),digest))
    hashes=tuple(records)
    if (not isinstance(value['input_hashes'],dict) or value['input_hashes']!=dict(hashes)):
        raise ValueError('synthetic input hashes or membership mismatch')
    return WorkerContext(path,expected_sha256,root,runtime,lock,gate,dataset,paths,hashes,limits)


def context_authorization_identity(config, context):
    """Cùng identity cho parent/child, không đọc nội dung learner qua DuckDB."""
    from . import authorization as auth
    context.validate_for(config)
    root=config.project_root.resolve()
    runtime=auth.preflight(config,project_root=root,runtime_report_path=context.runtime_report,
                           lock_file=context.lock_file)
    gate=auth.require_gate2_evidence(config,project_root=root,gate2_report=context.gate2_report,
                                    lock_file=context.lock_file,
                                    build_hashes_fn=lambda:auth.gate2_build_hashes(root))
    result=auth.identity(config,runtime,project_root=root,
                         canonical_manifest=context.data_paths.canonical_manifest,
                         assignments=context.data_paths.assignments,split_manifest=context.data_paths.split_manifest)
    return {**result,**context.identity,'build_hashes':auth.gate2_build_hashes(root),
            'gate2_report_sha256':gate['report_sha256'],'gate2_test_log_sha256':gate['test_log_sha256'],
            'gate2_pointer_sha256':gate['pointer_sha256']}


def context_from_options(options, config):
    path=getattr(options,'context_file',None)
    sha=getattr(options,'context_sha256',None)
    if path is None and sha is None:
        if config.phase=='cuda-smoke':raise ValueError('CUDA smoke requires a synthetic worker context')
        return None
    if path is None or sha is None:raise ValueError('both context file and SHA-256 are required')
    result=load_worker_context(path,expected_sha256=sha,project_root=config.project_root)
    return result.validate_for(config)
