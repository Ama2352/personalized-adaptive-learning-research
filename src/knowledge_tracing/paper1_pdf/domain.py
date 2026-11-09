"""Đọc prospective domain Paper2 cho simulator PDF Paper1, chỉ dữ liệu.

Nguồn reuse là lựa chọn triển khai mới, không historical PDF-byte identity.
Không đọc file khi import, không profile/RNG/policy/matrix/execution authority.
"""

import csv
from dataclasses import dataclass
import hashlib
import heapq
import io
import math
from pathlib import Path

from ..simulator_bridge import SimulatorBank, SimulatorItem, identity_hash
from .simulator import (
    PDF_SHA256, PROSPECTIVE_INPUT_SHA256, PROSPECTIVE_INPUT_VERSION, validate_prospective_domain,
)


ROOT = Path(__file__).resolve().parents[3]
INPUT_DIRECTORY = 'paper2/rivf2026_gam_kt_artifact_v20/rivf2026_gam_kt_artifact_v20/data/simulator_inputs'
INPUT_SHA256 = PROSPECTIVE_INPUT_SHA256
MAX_FILE_BYTES = 16*1024
MAX_TOTAL_BYTES = 64*1024
HEADERS = {
    'nodes.csv': ('concept_id',),
    'question_bank.csv': ('question_id', 'concept_id', 'elo_difficulty'),
    'concept_to_chapter_map.csv': ('concept_id', 'chapter'),
    'edges_baseline.csv': ('source', 'target'),
    'edges.csv': ('source', 'target'),
}
ROW_LIMITS = {'nodes.csv': 28, 'question_bank.csv': 84, 'concept_to_chapter_map.csv': 64,
              'edges_baseline.csv': 25, 'edges.csv': 31}


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _physical_file(name):
    _need(name in HEADERS and ROOT.is_absolute() and ROOT.is_dir()
          and ROOT.resolve() == ROOT.absolute() and not ROOT.is_symlink()
          and not getattr(ROOT, 'is_junction', lambda: False)(), 'physical fixed project root required')
    path = ROOT
    for part in (Path(INPUT_DIRECTORY)/name).parts:
        path /= part
        _need(not path.is_symlink() and not getattr(path, 'is_junction', lambda: False)(), 'input alias rejected')
    _need(path.resolve() == path.absolute() and path.is_file(), 'known regular input required')
    return path


def _read(name):
    path = _physical_file(name)
    size = path.stat().st_size
    _need(0 < size <= MAX_FILE_BYTES, 'per-file byte cap')
    with path.open('rb') as stream:
        raw = stream.read(MAX_FILE_BYTES+1)
    _need(len(raw) == size and len(raw) <= MAX_FILE_BYTES, 'stable bounded input bytes')
    return raw


def _rows(name, raw):
    try:
        text = raw.decode('utf-8-sig')
        _need('\x00' not in text, 'NUL in CSV')
        reader = csv.reader(io.StringIO(text, newline=''), strict=True)
        _need(tuple(next(reader, ())) == HEADERS[name], 'exact CSV header required')
        result = []
        for row in reader:
            _need(len(row) == len(HEADERS[name]) and all(value and value == value.strip()
                  and '\n' not in value and '\r' not in value for value in row), 'exact nonempty CSV fields required')
            result.append(tuple(row))
            _need(len(result) <= ROW_LIMITS[name], 'CSV row cap')
        return tuple(result)
    except (UnicodeError, csv.Error) as error:
        raise ValueError('invalid UTF8/CSV input') from error


def _lexicographic_order(nodes, edges):
    children = {node: [] for node in nodes}
    incoming = dict.fromkeys(nodes, 0)
    for parent, child in edges:
        children[parent].append(child)
        incoming[child] += 1
    ready = [node for node in nodes if incoming[node] == 0]
    heapq.heapify(ready)
    result = []
    while ready:
        node = heapq.heappop(ready)
        result.append(node)
        for child in children[node]:
            incoming[child] -= 1
            if incoming[child] == 0:
                heapq.heappush(ready, child)
    _need(len(result) == len(nodes), 'DAG traversal incomplete')
    return tuple(result)


@dataclass(frozen=True)
class Paper1PdfDomain:
    bank: SimulatorBank
    nodes: tuple[str, ...]
    chapters: tuple[tuple[str, str], ...]
    excluded_chapter_entries: tuple[tuple[str, str], ...]
    baseline_edges: tuple[tuple[str, str], ...]
    advanced_edges: tuple[tuple[str, str], ...]
    baseline_traversal_order: tuple[str, ...]
    advanced_traversal_order: tuple[str, ...]
    files: tuple[tuple[str, str, int], ...]
    canonical_candidate_pins: bool

    def metadata(self) -> dict:
        return dict(version=PROSPECTIVE_INPUT_VERSION, canonical_pdf_sha256=PDF_SHA256,
            bank_identity=self.bank.identity, nodes=self.nodes, chapters=self.chapters,
            excluded_chapter_entries=self.excluded_chapter_entries, baseline_edges=self.baseline_edges,
            advanced_edges=self.advanced_edges, baseline_traversal_order=self.baseline_traversal_order,
            advanced_traversal_order=self.advanced_traversal_order, files=self.files,
            input_directory=INPUT_DIRECTORY, canonical_candidate_pins=self.canonical_candidate_pins,
            source_bytes_verified=True, historical_pdf_input_identity_claimed=False,
            tie_order='lexicographic_topological_each_declared_graph', b0_policy_implemented=False,
            full_matrix_implemented=False, execution_authority=False)

    @property
    def identity(self) -> str:
        return identity_hash(self.metadata())


def load_prospective_paper2_domain() -> Paper1PdfDomain:
    """Đọc đúng5files đã pin, parse verified buffers rồi kiểm lại bytes.

    Chapter keys ngoài bank được trả riêng, không tự thêm vào28concept.
    Lexicographic order theo Unicode string, không locale; mỗi graph có order
    riêng. Caller còn phải chọn B0 topology khi triển khai policy đó sau này.
    """
    pins = tuple(INPUT_SHA256)
    _need(len(pins) == len(HEADERS) and len({name for name, _ in pins}) == len(pins)
          and {name for name, _ in pins} == set(HEADERS)
          and all(type(pin) is str and len(pin) == 64 and all(c in '0123456789abcdef' for c in pin)
                  for _, pin in pins), 'exact five declared input pins required')
    raw = {}
    total = 0
    for name, pin in pins:
        content = _read(name)
        total += len(content)
        _need(total <= MAX_TOTAL_BYTES and hashlib.sha256(content).hexdigest() == pin, 'input SHA/total byte cap')
        raw[name] = content
    parsed = {name: _rows(name, content) for name, content in raw.items()}
    nodes = tuple(row[0] for row in parsed['nodes.csv'])
    _need(len(nodes) == 28 and len(set(nodes)) == 28, 'exact28unique node IDs required')
    nodes = tuple(sorted(nodes))
    item_rows = parsed['question_bank.csv']
    _need(len(item_rows) == 84 and len({row[0] for row in item_rows}) == 84
          and all(row[1] in nodes for row in item_rows), 'exact84unique items in declared domain required')
    items = []
    for item_id, concept_id, difficulty in item_rows:
        value = float(difficulty)
        _need(math.isfinite(value), 'finite item difficulty required')
        items.append(SimulatorItem(item_id, concept_id, value))
    bank = SimulatorBank(PROSPECTIVE_INPUT_VERSION, tuple(items))
    chapter_rows = parsed['concept_to_chapter_map.csv']
    _need(len({row[0] for row in chapter_rows}) == len(chapter_rows), 'duplicate chapter key rejected')
    complete_map = dict(chapter_rows)
    _need(all(node in complete_map for node in nodes), 'missing domain chapter mapping')
    chapters = tuple((node, complete_map[node]) for node in nodes)
    excluded = tuple(sorted((node, chapter) for node, chapter in chapter_rows if node not in nodes))
    baseline = tuple(sorted(parsed['edges_baseline.csv']))
    advanced = tuple(sorted(parsed['edges.csv']))
    validate_prospective_domain(bank, chapters=dict(chapters), baseline_edges=baseline, advanced_edges=advanced)
    baseline_order = _lexicographic_order(nodes, baseline)
    advanced_order = _lexicographic_order(nodes, advanced)
    files = tuple(sorted((name, hashlib.sha256(raw[name]).hexdigest(), len(raw[name])) for name, _ in pins))
    for name, pin in pins:
        after = _read(name)
        _need(after == raw[name] and hashlib.sha256(after).hexdigest() == pin, 'input changed during domain load')
    return Paper1PdfDomain(bank, nodes, chapters, excluded, baseline, advanced, baseline_order, advanced_order,
                           files, pins == PROSPECTIVE_INPUT_SHA256)
