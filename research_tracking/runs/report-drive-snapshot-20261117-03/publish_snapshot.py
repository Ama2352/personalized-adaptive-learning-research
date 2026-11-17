"""Tái dùng publisher đã kiểm, lưu snapshot báo cáo mới sau nghiệm thu A2."""
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
BUNDLE=Path(__file__).resolve().parent
source=ROOT/'research_tracking/runs/report-drive-snapshot-20261117-01/publish_snapshot.py'
spec=importlib.util.spec_from_file_location('report_snapshot_v1',source)
publisher=importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)
publisher.BUNDLE=BUNDLE
publisher.NAME='research-reports-20261117-v3-calibration-a2'
publisher.PRIVATE=ROOT/'artifacts/akt/private/drive-upload/report-snapshot-20261117-03'

if __name__=='__main__':publisher.main()
