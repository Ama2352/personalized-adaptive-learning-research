"""Cấp Drive OAuth cho CPU worker Modal theo xác nhận của người dùng."""
import asyncio
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import warnings

ROOT = Path(__file__).resolve().parents[2]
PRIVATE = ROOT / 'artifacts/akt/private'
HERE = ROOT / 'research_tracking/runs/drive-cloud-artifacts-20261117-01'
SECRET_NAME = 'kltn-drive-artifacts-sang2005-20261117'


async def main():
    HERE.mkdir(exist_ok=True)
    output = HERE / 'SECRET_CREATION02.json'
    if output.exists():
        raise RuntimeError('Đã có biên nhận, cần rà trạng thái trước khi tạo lại Secret.')
    os.environ['MODAL_CONFIG_PATH'] = str(PRIVATE / 'modal2016.toml')
    os.environ['MODAL_PROFILE'] = 'kltn2016'
    os.environ['MODAL_LOGLEVEL'] = 'ERROR'
    logging.getLogger('modal').setLevel(logging.ERROR)
    from modal.client import _Client
    from modal_proto import api_pb2
    from google.auth.transport.requests import AuthorizedSession
    from google.oauth2.credentials import Credentials

    result = dict(status='STARTED', at=datetime.now(timezone.utc).isoformat(),
                  secret_name=SECRET_NAME, modal_workspace='honguyenminhsang2016',
                  drive_account='honguyenminhsang2005@gmail.com',
                  drive_parent='1vaojIEDvwtE-vZgjlybwzrsjrGNE_8O7',
                  user_authorization_vi='User cho phép tạo Secret, đích Drive Sang2005.',
                  secret_values_logged=False, gpu_function_called=False)
    client = None
    try:
        client = await asyncio.wait_for(_Client.from_env(), timeout=30)
        info = await asyncio.wait_for(client._stub.TokenInfoGet(api_pb2.TokenInfoGetRequest()), timeout=30)
        if info.workspace_name != result['modal_workspace']:
            raise RuntimeError('Modal workspace không khớp.')
        credentials = Credentials.from_authorized_user_file(str(PRIVATE / 'drive-upload/token.json'))
        with AuthorizedSession(credentials) as session:
            response = session.get('https://www.googleapis.com/drive/v3/about',
                                   params={'fields': 'user(emailAddress)'}, timeout=60)
            if response.status_code != 200 or response.json()['user']['emailAddress'] != result['drive_account']:
                raise RuntimeError('Drive account không khớp.')
            response = session.get('https://www.googleapis.com/drive/v3/files/' + result['drive_parent'],
                                   params={'fields': 'id,mimeType,trashed'}, timeout=60)
            if (response.status_code != 200 or response.json().get('trashed')
                    or response.json()['mimeType'] != 'application/vnd.google-apps.folder'):
                raise RuntimeError('Drive parent không truy cập được.')
        payload = json.loads(credentials.to_json())
        payload.pop('token', None)
        payload.pop('expiry', None)
        encoded = json.dumps(payload)
        if len(encoded) > 32768 or not all(payload.get(key) for key in ('client_id', 'client_secret', 'refresh_token')):
            raise RuntimeError('OAuth refresh credential không hợp lệ.')
        result['status'] = 'SECRET_CREATE_SENT'
        # Dùng cùng client/event loop cho mọi RPC, theo request của SDK 1.6.3.
        # Không trộn client async nội bộ với lớp public được synchronize.
        lookup = api_pb2.SecretGetOrCreateRequest(
            deployment_name=SECRET_NAME, environment_name='main',
            object_creation_type=api_pb2.OBJECT_CREATION_TYPE_UNSPECIFIED)
        exists = False
        try:
            await asyncio.wait_for(client._stub.SecretGetOrCreate(lookup), timeout=30)
            exists = True
        except Exception as error:
            from grpclib import GRPCError, Status
            if not isinstance(error, GRPCError) or error.status != Status.NOT_FOUND:
                raise
        if not exists:
            await asyncio.wait_for(client._stub.SecretGetOrCreate(api_pb2.SecretGetOrCreateRequest(
                deployment_name=SECRET_NAME, environment_name='main',
                object_creation_type=api_pb2.OBJECT_CREATION_TYPE_CREATE_FAIL_IF_EXISTS,
                env_dict={'KLTN_DRIVE_OAUTH_JSON': encoded})), timeout=30)
        await asyncio.wait_for(client._stub.SecretGetOrCreate(lookup), timeout=30)
        result.update(status='SECRET_CREATED_AND_HYDRATED', secret_key_names=['KLTN_DRIVE_OAUTH_JSON'],
                      reused_existing_without_overwrite=exists,
                      remote_identity_probe_required=True,
                      attach_policy='CPU artifact sync worker only; GPU function receives no Drive Secret')
    except Exception as error:
        result.update(error_type=type(error).__name__, status='FAILED_' + result['status'])
    finally:
        if client is not None:
            await asyncio.wait_for(client._close(), timeout=10)
        with output.open('x', encoding='utf-8') as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print(json.dumps(result, ensure_ascii=False))
    if result['status'] != 'SECRET_CREATED_AND_HYDRATED':
        raise SystemExit(1)


if __name__ == '__main__':
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', message=r'Your Modal token .*')
        asyncio.run(main())
