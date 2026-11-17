"""Đóng pin metadata A2/A3 qua API Volume, không thuê Modal compute."""
import asyncio
import json
import os
from pathlib import Path
import sys
import time
import warnings

ROOT = Path.cwd()
B = ROOT/'research_tracking/runs/junyi-calibration-real-20261117-01'
os.environ['MODAL_CONFIG_PATH'] = str(ROOT/'artifacts/akt/private/modal2016.toml')
os.environ['MODAL_PROFILE'] = 'kltn2016'
warnings.filterwarnings('ignore', message=r'Your Modal token .*')
sys.path.insert(0, str(ROOT/'scripts/akt'))
import modal
from modal_volume_archive import build_numeric_plan, validate_plan, zip_size


async def main():
    volume = modal.Volume.from_name('kltn-junyi-calibration-artifacts-v1', environment_name='main')
    for variant in ('A2', 'A3'):
        target = B/f'{variant}_NUMERIC_BACKUP_PLAN01.json'
        if target.exists():
            plan = json.loads(target.read_text())
            validate_plan(plan)
            print(variant, 'REUSE_PINNED_PLAN', len(plan['entries']), zip_size(plan), flush=True)
            continue
        gpu = json.loads((B/f'{variant}_GPU_RESULT01.json').read_text())
        assert gpu['status'] == 'STAGE_COMMITTED'
        started = time.monotonic()
        plan = await build_numeric_plan(volume, variant=variant,
            receipt_sha256=gpu['result']['receipt_sha256'], expected_counts=gpu['result']['counts'])
        with target.open('x', encoding='utf-8') as stream:
            json.dump(plan, stream, indent=2)
            stream.write('\n')
        print(variant, 'NUMERIC_BACKUP_PLAN_PINNED', len(plan['entries']), zip_size(plan),
              'seconds', round(time.monotonic()-started, 3), flush=True)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as error:
        print('METADATA_PLAN_STOPPED', type(error).__name__, flush=True)
        raise SystemExit(1) from None
