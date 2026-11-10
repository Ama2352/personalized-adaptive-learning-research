"""Ghép chín bộ file selected-only thành thống kê trên quần thể chung.

Đọc các refs trong request đã pin và có thể công bố gói review thống kê mới.
Chưa chọn winner, ghi freeze hoặc cấp quyền refit. Tái dùng accumulator đã cố định.
"""
from dataclasses import asdict, dataclass, replace
from contextlib import ExitStack
import hashlib
import math
import os
from pathlib import Path, PurePosixPath
import re
import time

from .research_admission import AdmissionLimits, MainAdmissionAccumulator, MainAdmissionStatistics, PopulationExpectation
from .research_selected_metadata import validate_selected_metadata, DOCUMENT_ROLES, ARTIFACT_ROLES
from .research_selected_rows import _exact_fields, normalize_selected_row
from .research_selection import REQUIRED_CANDIDATE_IDS
from .research_selection_io import BoundedArtifactReader, FileReadLimits, FileRef, need
from .research_selected_checkpoint import _json
from .akt.filesystem import publish_new_file

_publication_clock = time.perf_counter

REQUIRED_SOURCES = tuple('src/knowledge_tracing/' + name for name in (
    'research_admission.py', 'research_selection.py', 'research_population.py', 'research_selection_io.py',
    'research_selected_rows.py', 'research_selected_checkpoint.py', 'research_selected_metadata.py',
    'research_selected_files.py'))
REQUEST_KIND = 'MAIN_NINE_CACHED_STATISTICS_REQUEST_V1'
REQUEST_SCOPE = 'CACHED_STATISTICS_ONLY_NO_OPERATION_OR_SELECTION_GRANT'


@dataclass(frozen=True)
class SelectedFileStatistics:
    statistics: MainAdmissionStatistics
    verified_files: tuple[FileRef, ...]
    bytes_read: int
    index_entries: int
    elapsed_seconds: float
    operation_receipts_accepted: bool = False
    external_freeze_authority: bool = False
    main_refit_authorized: bool = False


@dataclass(frozen=True)
class StatisticsPublicationLimits:
    max_output_bytes: int
    max_file_bytes: int
    max_seconds: float

    def __post_init__(self):
        need(type(self.max_output_bytes) is int and type(self.max_file_bytes) is int
             and 8192 <= self.max_file_bytes <= self.max_output_bytes - 8192 <= 2**30,
             'Explicit output quota with failure reserve required')
        need(type(self.max_seconds) in (int, float) and math.isfinite(self.max_seconds)
             and 0 < self.max_seconds <= 120, 'Finite publication time cap required')


def _refs(document):
    need(type(document) is dict, 'FileRef mapping required')
    result = {}
    for key, value in document.items():
        _exact_fields(value, ('path', 'sha256', 'size_bytes'))
        result[key] = FileRef(**value)
    return result


def read_nine_selected_statistics(root, *, request_ref, population, io_limits, admission_limits):
    """Đọc request pin riêng, đối chiếu metadata và từng nhóm chín dòng K/y.

    population phải đến từ enumeration độc lập đã nghiệm thu. Đối tượng trả về
    vẫn giữ false cho operation/freeze/refit, kể cả khi đủ file và thống kê.
    """
    need(type(population) is PopulationExpectation and population.context.environment_id == 'grade10_simulator',
         'Trusted Grade10 population required; Junyi producer remains unavailable')
    need(type(io_limits) is FileReadLimits and type(admission_limits) is AdmissionLimits, 'Explicit typed limits required')
    admission_limits.__post_init__()
    verified = {}
    with BoundedArtifactReader(root, io_limits) as reader:
        request = reader.read_json(request_ref)
        verified[request_ref.path] = request_ref
        _exact_fields(request, ('schema_version', 'kind', 'scope', 'population', 'candidates', 'source_inventory'))
        need(type(request['schema_version']) is int and request['schema_version'] == 1
             and request['kind'] == REQUEST_KIND and request['scope'] == REQUEST_SCOPE, 'Statistics request scope/version')
        need(_json(request['population']) == _json(asdict(population)), 'Request independent population mismatch')
        _exact_fields(request['candidates'], REQUIRED_CANDIDATE_IDS)
        source_refs = _refs(request['source_inventory'])
        need(set(source_refs) == set(REQUIRED_SOURCES) and all(logical == ref.path for logical, ref in source_refs.items()),
             'Exact canonical validator/core source inventory required')

        def verify(ref):
            previous = verified.get(ref.path)
            need(previous is None or previous == ref, 'Conflicting input FileRef')
            reader.verify_file(ref)
            verified[ref.path] = ref

        for ref in source_refs.values():
            verify(ref)
        claims, indices = {}, {}
        for candidate in REQUIRED_CANDIDATE_IDS:
            descriptor = request['candidates'][candidate]
            _exact_fields(descriptor, ('artifacts', 'expected_claim_binding', 'expected_checkpoint_identity', 'producer_source_files'))
            _exact_fields(descriptor['artifacts'], ARTIFACT_ROLES)
            refs = _refs(descriptor['artifacts'])
            sources = _refs(descriptor['producer_source_files'])
            for ref in (*refs.values(), *sources.values()):
                verify(ref)
            documents = {role: reader.read_json(refs[role]) for role in DOCUMENT_ROLES}
            claim = validate_selected_metadata(documents=documents, artifact_refs=refs,
                expected_claim_binding=descriptor['expected_claim_binding'],
                expected_checkpoint_identity=descriptor['expected_checkpoint_identity'],
                producer_source_files=sources, population=population)
            need(claim.candidate_id == candidate, 'Request candidate key/body mismatch')
            claims[candidate] = claim
            indices[candidate] = {kind: reader.index_csv(refs[kind], candidate_id=candidate, kind=kind)
                                  for kind in ('predictions', 'targets')}
        remaining = min(admission_limits.max_seconds, io_limits.max_seconds - reader._guard())
        need(remaining > 0, 'No remaining cumulative admission time')
        accumulator = MainAdmissionAccumulator(population, replace(admission_limits, max_seconds=remaining))
        for candidate in REQUIRED_CANDIDATE_IDS:
            accumulator.add_candidate(claims[candidate])
        accumulator.seal_candidate_claims()
        keys = indices['A0']['targets'].keys
        need(len(keys) == population.full_targets and all(index.keys == keys
             for pair in indices.values() for index in pair.values()), 'All nine full prediction/target keys required')
        with ExitStack() as stack:
            row_readers = indices
            if io_limits.max_open_files >= 2 * len(REQUIRED_CANDIDATE_IDS):
                row_readers = {candidate: {kind: stack.enter_context(index.open_rows())
                    for kind, index in pair.items()} for candidate, pair in indices.items()}
            for key in keys:
                rows = tuple(normalize_selected_row(row_readers[candidate]['predictions'].row(key),
                    row_readers[candidate]['targets'].row(key), claims[candidate]) for candidate in REQUIRED_CANDIDATE_IDS)
                accumulator.add_row_group(rows)
            statistics = accumulator.finish()
        final = reader.verify_unchanged()
        result = SelectedFileStatistics(statistics, tuple(verified[path] for path in sorted(verified)),
            final['bytes_read'], final['index_entries'], final['elapsed_seconds'])
        reader._guard()
        return result


def _review_directory(root, relative):
    need(type(relative) is str, 'Relative review directory required')
    path = PurePosixPath(relative)
    need(len(path.parts) == 3 and path.parts[:2] == ('research_tracking', 'runs')
         and path.as_posix() == relative and re.fullmatch('[a-z0-9][a-z0-9_-]{2,100}', path.name) is not None,
         'One named review run under research_tracking/runs required')
    cursor = root
    for part in ('', *path.parts):
        cursor = cursor / part
        need(not cursor.is_symlink() and not getattr(cursor, 'is_junction', lambda: False)(),
             'Review directory ancestor alias forbidden')
    need(root.resolve() == root and cursor.resolve() == cursor and cursor.parent.is_dir(),
         'Physical existing review parent required')
    return cursor


def publish_nine_statistics_review(root, *, request_ref, population, output_directory, atomic_publisher_ref,
                                   io_limits, admission_limits, publication_limits):
    """Ghi review thống kê mới, giữ failure ưu tiên hơn COMPLETE khi có lỗi muộn.

    COMPLETE chỉ mô tả gói cached statistics. Caller phải nghiệm thu operation
    sau khi hàm trả về. Chưa có quyền selection, external freeze hoặc refit.
    """
    need(type(publication_limits) is StatisticsPublicationLimits, 'Typed publication limits required')
    publication_limits.__post_init__()
    need(type(atomic_publisher_ref) is FileRef
         and atomic_publisher_ref.path == 'src/knowledge_tracing/akt/filesystem.py', 'Pinned atomic publisher required')
    started = _publication_clock()
    root = Path(root).absolute()
    directory = _review_directory(root, output_directory)
    need(not directory.exists(), 'Never overwrite an existing review run')
    total_seconds = min(io_limits.max_seconds, publication_limits.max_seconds)

    def guard():
        elapsed = _publication_clock() - started
        need(math.isfinite(elapsed) and 0 <= elapsed < total_seconds, 'Publication cumulative deadline exceeded')
        need(_review_directory(root, output_directory) == directory, 'Review directory changed')
        return elapsed

    result = read_nine_selected_statistics(root, request_ref=request_ref, population=population,
        io_limits=replace(io_limits, max_seconds=total_seconds), admission_limits=admission_limits)
    input_refs = (*result.verified_files, atomic_publisher_ref)
    guard()
    remaining_bytes = io_limits.max_total_read_bytes - result.bytes_read
    need(remaining_bytes >= io_limits.max_file_bytes, 'No remaining cumulative input byte budget')
    directory.mkdir(exist_ok=False)
    written_bytes, outputs = 0, {}

    def write(name, payload):
        nonlocal written_bytes
        guard()
        raw = (_json(payload) + '\n').encode('utf-8')
        need(len(raw) <= publication_limits.max_file_bytes
             and written_bytes + len(raw) <= publication_limits.max_output_bytes - 8192,
             'Publication output quota before write')
        path = directory / name
        with path.open('xb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        written_bytes += len(raw)
        with path.open('rb') as stream:
            need(stream.read(len(raw) + 1) == raw, 'Publication readback mismatch')
        guard()
        return FileRef(path.relative_to(root).as_posix(), hashlib.sha256(raw).hexdigest(), len(raw))

    def verify_outputs():
        guard()
        for ref in outputs.values():
            path = root / ref.path
            need(not path.is_symlink() and path.is_file() and path.stat().st_size == ref.size_bytes,
                 'Publication output identity/size mismatch')
            with path.open('rb') as stream:
                raw = stream.read(ref.size_bytes + 1)
            need(len(raw) == ref.size_bytes and hashlib.sha256(raw).hexdigest() == ref.sha256,
                 'Publication output SHA mismatch')
        guard()

    try:
        outputs['statistics.json'] = write('statistics.json', asdict(result.statistics))
        outputs['coverage.json'] = write('coverage.json', dict(full_targets=result.statistics.full_targets,
            common_targets=result.statistics.common_targets, learners=[asdict(row) for row in result.statistics.learner_coverage],
            candidates=[asdict(row) for row in result.statistics.candidate_coverage]))
        outputs['input-inventory.json'] = write('input-inventory.json', dict(request=asdict(request_ref),
            population=asdict(population), files=[asdict(ref) for ref in input_refs],
            operation_receipts_accepted=False, external_freeze_authority=False, main_refit_authorized=False))
        remaining_seconds = total_seconds - guard()
        verification_limits = replace(io_limits, max_total_read_bytes=remaining_bytes, max_seconds=remaining_seconds)
        with BoundedArtifactReader(root, verification_limits) as reader:
            for ref in input_refs:
                reader.verify_file(ref)
            verify_outputs()
            complete = dict(schema_version=1, status='COMPLETE_CACHED_NINE_STATISTICS_REVIEW_V1',
                scope=REQUEST_SCOPE, request_sha256=request_ref.sha256,
                outputs={name: asdict(ref) for name, ref in outputs.items()},
                operation_receipts_accepted=False, external_freeze_authority=False,
                main_refit_authorized=False, actual_model_selection=False,
                failure_marker='FAILURE.json', caller_operation_acceptance_required=True)
            pending = write('COMPLETE.pending.json', complete)
            guard()
            publish_new_file(root / pending.path, directory / 'COMPLETE.json')
            complete_ref = FileRef((directory / 'COMPLETE.json').relative_to(root).as_posix(), pending.sha256, pending.size_bytes)
            outputs['COMPLETE.json'] = complete_ref
            guard()
            reader.verify_unchanged()
            need(result.bytes_read + reader.bytes_read <= io_limits.max_total_read_bytes, 'Cumulative input quota exceeded')
            verify_outputs()
            need({path.name for path in directory.iterdir()} == set(outputs), 'Unexpected publication file')
            guard()
        return complete_ref
    except BaseException as error:
        failure = dict(status='FAILED_CACHED_STATISTICS_REVIEW_DO_NOT_ACCEPT', error_type=type(error).__name__,
            error=str(error)[:512], COMPLETE_is_not_authority=True, automatic_retry=False,
            external_freeze_authority=False, main_refit_authorized=False)
        try:
            _review_directory(root, output_directory)
            raw = (_json(failure) + '\n').encode('utf-8')
            need(len(raw) <= 8192 and written_bytes + len(raw) <= publication_limits.max_output_bytes,
                 'Reserved failure quota')
            with (directory / 'FAILURE.json').open('xb') as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
        except BaseException as secondary:
            error.add_note('Failure receipt unavailable: ' + type(secondary).__name__)
        raise
