"""Đọc trạng thái function và billing, không tạo tài nguyên tính toán."""
import asyncio
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
os.environ['MODAL_CONFIG_PATH'] = str(ROOT / 'artifacts/akt/private/modal.toml')
os.environ['MODAL_PROFILE'] = 'kltn'
from modal.client import _Client
from modal_proto import api_pb2
from google.protobuf.json_format import MessageToDict


async def inspect(app_id):
    client = await _Client.from_env()
    try:
        layout = await asyncio.wait_for(client._stub.AppGetLayout(
            api_pb2.AppGetLayoutRequest(app_id=app_id)), 15)
        functions = []
        for function_id in layout.app_layout.function_ids.values():
            stats = await asyncio.wait_for(client._stub.FunctionGetCurrentStats(
                api_pb2.FunctionGetCurrentStatsRequest(function_id=function_id)), 15)
            functions.append(dict(function_id=function_id, stats=MessageToDict(
                stats, preserving_proto_field_name=True,
                always_print_fields_with_no_presence=True)))
        return dict(app_id=app_id, observed_at_utc=datetime.now(timezone.utc).isoformat(),
                    functions=functions)
    finally:
        await client._close()


if __name__ == '__main__':
    result = asyncio.run(inspect(sys.argv[1]))
    output = Path(__file__).resolve().parent / sys.argv[2]
    assert output.parent == Path(__file__).resolve().parent
    with output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps(result))
