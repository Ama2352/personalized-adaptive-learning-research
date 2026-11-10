"""Ghép chín bộ file selected-only thành thống kê trên quần thể chung.

Chỉ đọc các refs trong request đã pin. Chưa nghiệm thu operation/late-failure,
chọn winner, ghi freeze hoặc cấp quyền refit. Tái dùng accumulator đã cố định.
"""
from dataclasses import asdict, dataclass, replace
from contextlib import ExitStack

from .research_admission import AdmissionLimits, MainAdmissionAccumulator, MainAdmissionStatistics, PopulationExpectation
from .research_selected_metadata import validate_selected_metadata, DOCUMENT_ROLES, ARTIFACT_ROLES
from .research_selected_rows import _exact_fields, normalize_selected_row
from .research_selection import REQUIRED_CANDIDATE_IDS
from .research_selection_io import BoundedArtifactReader, FileReadLimits, FileRef, need
from .research_selected_checkpoint import _json

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
