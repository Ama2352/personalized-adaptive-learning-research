#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"
BKT_VENV="${JUNYI_BKT_VENV:-/opt/junyi-bkt/venv}"
RUN_DIR="${PROJECT_ROOT}/experiments/bkt_baseline/results/wsl_cpp/cv_cpp"
export PYTHONPYCACHEPREFIX="${RUN_DIR}/pycache"
export TMPDIR="${RUN_DIR}/tmp"
export PYTHONPATH="${PROJECT_ROOT}/src"
echo "CV runner start: $(date -u +%FT%TZ)"
exec "${BKT_VENV}/bin/python" "${PROJECT_ROOT}/scripts/wsl2/run_cpp_cv.py" >> "${RUN_DIR}/run.log" 2>&1
