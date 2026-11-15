"""Đọc đúng workspace và billing trước chuyển đợt ngân sách; không cấp máy."""
import asyncio
from datetime import datetime, timezone
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


async def main():
    expected = ROOT / 'artifacts/akt/private/modal2016.toml'
    assert Path(os.environ['MODAL_CONFIG_PATH']).resolve() == expected.resolve()
    assert os.environ['MODAL_PROFILE'] == 'kltn2016'
    from modal.client import _Client
    from modal_proto import api_pb2
    from google.protobuf.timestamp_pb2 import Timestamp
    from google.protobuf.json_format import MessageToDict

    client = await _Client.from_env()
    try:
        info = await asyncio.wait_for(client._stub.TokenInfoGet(api_pb2.TokenInfoGetRequest()), 15)
        assert info.workspace_name == 'honguyenminhsang2016'
        start = Timestamp()
        start.FromDatetime(datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0))
        response = await asyncio.wait_for(client._stub.WorkspaceBillingSummary(
            api_pb2.WorkspaceBillingSummaryRequest(start_timestamp=start)), 15)
        record = dict(status='VERIFIED_NEW_WORKSPACE_READ_ONLY', workspace=info.workspace_name,
                      observed_at_utc=datetime.now(timezone.utc).isoformat(),
                      billing=MessageToDict(response, preserving_proto_field_name=True),
                      user_reported_available_credit_usd=30, paid_gpu_started=False)
        path = HERE / 'workspace2016-preflight01.json'
        with path.open('x', encoding='utf-8') as stream:
            json.dump(record, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
        print(json.dumps(record, ensure_ascii=False))
    finally:
        await client._close()


if __name__ == '__main__':
    asyncio.run(main())
