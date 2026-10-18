"""Local paths and resource gates for the research benchmark."""

from pathlib import Path
import shutil

import psutil


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CSV = PROJECT_ROOT / "dataset" / "junyi_ProblemLog_original.csv"
DEFAULT_ARTIFACTS = PROJECT_ROOT / "artifacts" / "bkt_baseline"


def preflight(output_dir: str | Path, *, min_free_gb: int = 2) -> dict:
    output = Path(output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    free_disk = shutil.disk_usage(output).free
    available_ram = psutil.virtual_memory().available
    if free_disk < min_free_gb * 10**9:
        raise RuntimeError(f"Need at least {min_free_gb} GB free on {output.anchor}")
    if available_ram < 2 * 10**9:
        raise RuntimeError("Need at least 2 GB available RAM for bounded processing")
    return {"free_disk_bytes": free_disk, "available_ram_bytes": available_ram}
