"""Đọc packet throughput TRAIN80 có scope partial rõ ràng, không Torch."""
import hashlib
import json
from pathlib import Path

from knowledge_tracing.akt.config import PROJECT_ROOT
from knowledge_tracing.akt.research_junyi_data import JunyiPhaseView, load_prepared_junyi_encoding
from knowledge_tracing.akt.research_junyi_roles import JunyiResearchRoles
from knowledge_tracing.akt.research_junyi_window_cache import _load_shard, _parts, _encoding_guard
from knowledge_tracing.akt.types import TrainingWindow

KIND = 'JUNYI_TRAIN80_THROUGHPUT_PACKET_V1'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def need(condition, message):
    if not condition:
        raise ValueError(message)


class JunyiTrainingPacket:
    """Giữ full source view cho membership, packet identity cho workload subset."""
    def __init__(self, packet_root, *, expected_packet_sha256):
        root = Path(packet_root).absolute()
        allowed = PROJECT_ROOT/'artifacts/akt/modal/junyi-throughput-20261112-01'
        need(root.is_relative_to(allowed) and root.resolve() == root, 'Owned throughput packet required')
        self.root = root
        self.identity = expected_packet_sha256
        self._control_pin = expected_packet_sha256
        need(sha(root/'packet.json') == expected_packet_sha256, 'Packet manifest changed')
        self.manifest = json.loads((root/'packet.json').read_text())
        need(self.manifest.get('kind') == KIND and self.manifest.get('status') == 'PREPARED_PARTIAL_ENGINEERING_PACKET'
             and self.manifest.get('full_role_coverage') is False
             and self.manifest.get('full_train_epoch_complete') is False, 'Explicit partial engineering scope required')
        for name, entry in self.manifest['files'].items():
            path = self._file(name)
            need(path.stat().st_size == entry['bytes'] and sha(path) == entry['sha256'], 'Packet file changed')
        source = json.loads(self._file('full-cache-manifest.json').read_text())
        self.source_manifest = source
        need(source['status'] == 'COMPLETE' and source['key'] == self.manifest['source_key'], 'Source cache binding mismatch')
        role_payload = json.loads(self._file('roles.json').read_text())
        for name in ('train_users', 'selection_users', 'calibration_users', 'outer_validation_users'):
            role_payload[name] = tuple(role_payload[name])
        roles = JunyiResearchRoles(**role_payload)
        self.source_train_view = JunyiPhaseView(roles, 'select_train80', roles.train_users, roles.identity)
        need(self.source_train_view.identity == source['key']['phase_view_identity'], 'Source TRAIN80 role mismatch')
        pins = self.manifest['files']
        self.encoding = load_prepared_junyi_encoding(self._file('encoding.json'), self._file('encoding-receipt.json'),
            view=self.source_train_view, source_data_sha256=source['key']['source_data_sha256'],
            expected_file_sha256=pins['encoding.json']['sha256'],
            expected_receipt_sha256=pins['encoding-receipt.json']['sha256'])
        need(self.encoding.identity == source['key']['encoding_identity']
             and len(self.encoding.native.vocabulary.values) == 717, 'Full TRAIN80 encoding717 required')
        self._allowed_users = frozenset(self.source_train_view.users)
        self.expected = dict(windows=1024, targets=56332, tokens=100032, learners=755)
        need(self.manifest['expected'] == self.expected and len(self.manifest['selected_shards']) == 16,
             'Frozen packet workload mismatch')
        source_shards = {entry['name']: entry for entry in source['shards']}
        seen = set()
        for selection in self.manifest['selected_shards']:
            name, indexes = selection['name'], selection['record_indexes']
            need(name in source_shards and name not in seen and Path(name).name == name
                 and type(indexes) is list and len(indexes) == 64
                 and all(type(index) is int and 0 <= index < source_shards[name]['records'] for index in indexes)
                 and indexes == sorted(set(indexes)), 'Invalid selected shard/index list')
            seen.add(name)
            need(pins['shards/'+name]['sha256'] == source_shards[name]['sha256'], 'Original shard identity mismatch')
        self._shards = source_shards
        self.full_role_coverage = False
        self.full_train_epoch_complete = False

    def _file(self, name):
        relative = Path(name)
        need(not relative.is_absolute() and '..' not in relative.parts, 'Unsafe packet member')
        path = self.root/relative
        current = path
        while current != PROJECT_ROOT:
            need(not current.is_symlink() and not getattr(current, 'is_junction', lambda: False)(), 'Packet path alias rejected')
            current = current.parent
        return path

    def _guard(self):
        need(sha(self._file('packet.json')) == self._control_pin, 'Packet manifest changed')
        _encoding_guard(self.encoding, self.source_manifest['key'])

    def iter_training_windows(self):
        """Chỉ target record được chọn, geometry/ranks gốc giữ nguyên."""
        self._guard()
        count = targets = tokens = 0
        users = set(); target_rows = set()
        for selection in self.manifest['selected_shards']:
            chosen = set(selection['record_indexes'])
            path = self._file('shards/'+selection['name'])
            entry = self._shards[selection['name']]
            matched = 0
            for index, record in enumerate(_load_shard(path, entry, self.source_manifest)):
                if index not in chosen:
                    continue
                need(type(record) is TrainingWindow, 'Packet only accepts training windows')
                metadata, arrays, selected_targets = _parts(record, self.source_train_view, self.encoding, self._allowed_users)
                for _, _, source_row in selected_targets:
                    need(source_row not in target_rows, 'Packet target duplicated')
                    target_rows.add(source_row)
                count += 1; matched += 1; targets += len(selected_targets); tokens += len(arrays['item_ids'])
                users.add(metadata['user_id'])
                yield record
            need(matched == len(chosen), 'Selected packet record missing')
        need(dict(windows=count, targets=targets, tokens=tokens, learners=len(users)) == self.expected,
             'Partial packet population mismatch')
        self._guard()

    def verify(self):
        for _ in self.iter_training_windows():
            pass
        return dict(status='VERIFIED_PARTIAL_TRAIN80_PACKET', **self.expected,
                    full_role_coverage=False, full_train_epoch_complete=False,
                    packet_sha256=self.identity, source_encoding_identity=self.encoding.identity)
