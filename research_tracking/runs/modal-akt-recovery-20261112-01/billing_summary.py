"""Đọc billing theo tháng UTC, chỉ xuất số liệu và không tạo compute."""
import os,json,asyncio,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[3]
os.environ['MODAL_CONFIG_PATH']=str(ROOT/'artifacts/akt/private/modal.toml')
os.environ['MODAL_PROFILE']='kltn'
from modal.client import _Client
from modal_proto import api_pb2
from google.protobuf.timestamp_pb2 import Timestamp
from google.protobuf.json_format import MessageToDict
async def main():
    client=await _Client.from_env()
    try:
        start=Timestamp();start.FromDatetime(datetime.now(timezone.utc).replace(day=1,hour=0,minute=0,second=0,microsecond=0))
        value=await asyncio.wait_for(client._stub.WorkspaceBillingSummary(api_pb2.WorkspaceBillingSummaryRequest(start_timestamp=start)),10)
        return dict(status='READ',observed_at_utc=datetime.now(timezone.utc).isoformat(),billing=MessageToDict(value,preserving_proto_field_name=True))
    finally:
        await client._close()
result=asyncio.run(main())
output=ROOT/'research_tracking/runs/modal-akt-recovery-20261112-01'/sys.argv[1]
assert output.parent==ROOT/'research_tracking/runs/modal-akt-recovery-20261112-01'
with output.open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2);stream.write('\n')
print(json.dumps(result))
