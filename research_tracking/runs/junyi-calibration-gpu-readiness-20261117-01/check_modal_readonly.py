"""Đọc TokenInfo và billing workspace đã ghim, không tạo App/function/volume."""
import asyncio
import argparse
from datetime import datetime, timezone
import importlib.metadata
import json
import logging
import os
from pathlib import Path
import warnings

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


async def main(destination):
    config = ROOT / 'artifacts/akt/private/modal2016.toml'
    result = dict(status='READ_ONLY_CHECK_STARTED', at=datetime.now(timezone.utc).isoformat(),
                  expected_workspace='honguyenminhsang2016', profile='kltn2016',
                  config_file=config.relative_to(ROOT).as_posix(),
                  modal_version=importlib.metadata.version('modal'),
                  paid_function_called=False, provision_requested=False)
    if not config.is_file():
        result['status'] = 'CONFIG_MISSING'
    else:
        os.environ['MODAL_CONFIG_PATH'] = str(config)
        os.environ['MODAL_PROFILE'] = 'kltn2016'
        os.environ['MODAL_LOGLEVEL'] = 'ERROR'
        logging.getLogger('modal').setLevel(logging.ERROR)
        from modal.client import _Client
        from modal_proto import api_pb2
        from google.protobuf.timestamp_pb2 import Timestamp
        from google.protobuf.json_format import MessageToDict
        client = None
        try:
            client = await asyncio.wait_for(_Client.from_env(), 20)
            info = await asyncio.wait_for(client._stub.TokenInfoGet(api_pb2.TokenInfoGetRequest()), 15)
            result.update(workspace=info.workspace_name, token_valid=True)
            # Chỉ lấy timestamp, không ghi token ID/workspace ID hoặc user identity.
            if info.HasField('expires_at'):
                result['token_expires_at'] = info.expires_at.ToJsonString()
            if info.workspace_name != 'honguyenminhsang2016':
                result['status'] = 'WORKSPACE_MISMATCH_NO_BILLING_QUERY'
            else:
                start = Timestamp()
                start.FromDatetime(datetime.now(timezone.utc).replace(day=1, hour=0, minute=0,
                                                                    second=0, microsecond=0))
                billing = await asyncio.wait_for(client._stub.WorkspaceBillingSummary(
                    api_pb2.WorkspaceBillingSummaryRequest(start_timestamp=start)), 15)
                result.update(status='TOKEN_AND_BILLING_READ_ONLY_VERIFIED',
                              billing=MessageToDict(billing, preserving_proto_field_name=True))
        except Exception as error:
            # Không ghi message/traceback vì lỗi transport có thể chứa cấu hình riêng.
            message = str(error).lower()
            result.update(status='READ_ONLY_CHECK_FAILED', error_type=type(error).__name__,
                          token_expired_message='expired' in message,
                          token_revoked_message='revoked' in message,
                          error_requires_authentication=any(x in message for x in ('unauthenticated', 'authentication', 'token')))
        finally:
            if client is not None:
                await client._close()
    HERE.mkdir(parents=True, exist_ok=True)
    with destination.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=HERE / 'MODAL_READ_ONLY.json')
    args = parser.parse_args()
    if args.output.resolve().parent != HERE.resolve() or args.output.exists():
        parser.error('Output mới phải nằm trong bundle của lượt kiểm.')
    with warnings.catch_warnings():
        # SDK cảnh báo expiry có thể in token ID. Expiry đã được lấy bằng field whitelist.
        warnings.filterwarnings('ignore', message=r'Your Modal token .*')
        asyncio.run(main(args.output))
