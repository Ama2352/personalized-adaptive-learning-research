"""Kích thước phải do caller chọn; không mặc định scientific protocol."""

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class SAKTConfig:
    num_items: int
    max_length: int
    d_model: int
    num_heads: int
    head_dim: int
    dropout: float
    layer_norm_eps: float

    def __post_init__(self) -> None:
        for field in ('num_items', 'max_length', 'd_model', 'num_heads', 'head_dim'):
            value = getattr(self, field)
            if type(value) is not int or value <= 0:
                raise ValueError(f'{field} must be a positive integer')
        if (isinstance(self.dropout, bool) or not isinstance(self.dropout, (int, float))
                or not math.isfinite(self.dropout) or not 0 <= self.dropout < 1):
            raise ValueError('dropout must be finite and in [0, 1)')
        if (isinstance(self.layer_norm_eps, bool)
                or not isinstance(self.layer_norm_eps, (int, float))
                or not math.isfinite(self.layer_norm_eps) or self.layer_norm_eps <= 0):
            raise ValueError('layer_norm_eps must be finite and positive')
