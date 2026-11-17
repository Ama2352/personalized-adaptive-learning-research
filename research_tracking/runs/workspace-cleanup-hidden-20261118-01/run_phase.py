"""Tái dùng công cụ đã kiểm với bundle và prefix riêng, không ghi đè đợt trước."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'research_tracking/runs/workspace-cleanup-20261118-01'))
mode=sys.argv[1]
if mode=='pack':
    import pack_bulk as worker
    worker.B=B;worker.WORK=ROOT/'artifacts/akt/runtime/workspace-cleanup-hidden-20261118-01/packages';worker.PREFIX='HIDDEN_FIXTURE_CONTENT'
elif mode=='upload':
    import upload_bulk as worker
    worker.B=B
elif mode=='plan':
    import make_bulk_plan as worker
    worker.B=B
else:raise ValueError('Chỉ nhận pack/upload/plan')
worker.main()
