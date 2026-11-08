"""Minimal adapter for the graph-free GAM-KT source implementation."""
from collections.abc import Mapping

from .original_junyi import GAMKTModel, configure_metadata


def build_model(topic_map: Mapping[str, str], area_map: Mapping[str, str]) -> GAMKTModel:
    configure_metadata(topic_map, area_map)
    return GAMKTModel(
        use_graph_context=False,
        time_decay_rate=0.0,
        graph_weight=0.0,
        graph_source=None,
        graph_signal_enabled=False,
        graph_adaptation_enabled=False,
        name="GAM-KT",
    )
