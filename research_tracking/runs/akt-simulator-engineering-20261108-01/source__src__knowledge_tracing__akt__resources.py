"""Lightweight process and system memory snapshots for AKT guards."""

from __future__ import annotations

import os

import psutil


def memory_snapshot() -> dict:
    """Return process-local RSS and system-wide available RAM, with units explicit."""
    info = psutil.Process(os.getpid()).memory_info()
    peak = getattr(info, 'peak_wset', None)
    vm = psutil.virtual_memory()
    return {
        'pid': os.getpid(),
        'process_rss_bytes': int(info.rss),
        'process_peak_rss_bytes': int(peak) if peak is not None else None,
        'system_available_ram_bytes': int(vm.available),
        'system_total_ram_bytes': int(vm.total),
    }
