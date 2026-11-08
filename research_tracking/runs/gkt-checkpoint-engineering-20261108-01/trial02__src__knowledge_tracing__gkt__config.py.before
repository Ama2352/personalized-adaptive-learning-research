"""Geometry và semantics caller-explicit của kernel GKT chưa hoàn chỉnh."""

from dataclasses import dataclass
import hashlib
import json
import re


@dataclass(frozen=True)
class GKTKernelConfig:
    num_nodes: int
    state_dim: int
    embedding_dim: int
    message_dim: int
    adjacency_kind: str
    node_unit: str
    require_zero_diagonal: bool
    require_nonnegative: bool

    def __post_init__(self):
        for name in ('num_nodes', 'state_dim', 'embedding_dim', 'message_dim'):
            if type(getattr(self, name)) is not int or getattr(self, name) <= 0:
                raise ValueError(f'{name} must be a positive integer')
        if self.adjacency_kind not in ('static', 'dense'):
            raise ValueError('only caller static or paper Dense adjacency is supported')
        if self.node_unit not in ('concept', 'exercise_tag'):
            raise ValueError('node_unit must explicitly identify concept or exercise_tag')
        if self.require_zero_diagonal is not True or self.require_nonnegative is not True:
            raise ValueError('this kernel requires zero diagonal and nonnegative adjacency')


@dataclass(frozen=True)
class GKTBinding:
    domain: str
    vocabulary_sha256: str
    node_ids: tuple[str, ...]
    node_unit: str

    def __post_init__(self):
        if not isinstance(self.domain, str) or not self.domain.strip():
            raise ValueError('explicit domain is required')
        if not isinstance(self.vocabulary_sha256, str) or not re.fullmatch(r'[0-9a-f]{64}', self.vocabulary_sha256):
            raise ValueError('vocabulary_sha256 must be a lowercase SHA256')
        if (type(self.node_ids) is not tuple or not self.node_ids
                or any(not isinstance(x, str) or not x for x in self.node_ids)
                or len(set(self.node_ids)) != len(self.node_ids)):
            raise ValueError('ordered unique node IDs are required')
        if self.node_unit not in ('concept', 'exercise_tag'):
            raise ValueError('invalid node unit')

    @property
    def node_order_sha256(self):
        payload = json.dumps(self.node_ids, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
        return hashlib.sha256(payload).hexdigest()
