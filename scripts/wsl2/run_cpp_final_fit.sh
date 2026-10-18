#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"
BKT_VENV="${JUNYI_BKT_VENV:-/opt/junyi-bkt/venv}"
RUN_DIR="${PROJECT_ROOT}/experiments/bkt_baseline/results/wsl_cpp/final_cpp"
export PYTHONPYCACHEPREFIX="${RUN_DIR}/pycache"
export TMPDIR="${RUN_DIR}/tmp"
export PYTHONPATH="${PROJECT_ROOT}/src"
mkdir -p "$PYTHONPYCACHEPREFIX" "$TMPDIR"
"${BKT_VENV}/bin/python" -m py_compile "${PROJECT_ROOT}/scripts/wsl2/run_cpp_final_fit.py"
exec "${BKT_VENV}/bin/python" "${PROJECT_ROOT}/scripts/wsl2/run_cpp_final_fit.py"
