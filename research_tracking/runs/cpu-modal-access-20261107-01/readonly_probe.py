"""Chỉ đọc TokenInfoGet/WorkspaceSettings; không in token hoặc tạo compute."""
import asyncio,json,logging,os,sys
from datetime import datetime,timezone
from pathlib import Path
root=Path(sys.argv[1]).resolve()
for key in ('MODAL_TOKEN_ID','MODAL_TOKEN_SECRET','MODAL_OAUTH_REFRESH_TOKEN','MODAL_OAUTH_CLIENT_ID','MODAL_OAUTH_CLIENT_SECRET','MODAL_OAUTH_JWT_KEY'):
    os.environ.pop(key,None)
os.environ['MODAL_CONFIG_PATH']=str(root/'artifacts/akt/private/modal.toml')
os.environ['MODAL_PROFILE']='kltn'
os.environ['MODAL_LOGLEVEL']='CRITICAL'
logging.disable(logging.CRITICAL)
from modal.client import _Client
from modal_proto import api_pb2
from google.protobuf import empty_pb2
async def inspect():
    client=None
    try:
        client=await _Client.from_env()
        token=await asyncio.wait_for(client._stub.TokenInfoGet(api_pb2.TokenInfoGetRequest()),timeout=10)
        match=token.workspace_name=='honguyenminhsang2005'
        out={'authenticated':True,'workspace_name':token.workspace_name,'workspace_matches_expected':match,
             'created_at_utc':token.created_at.ToDatetime(tzinfo=timezone.utc).isoformat() if token.HasField('created_at') else None,
             'expires_at_utc':token.expires_at.ToDatetime(tzinfo=timezone.utc).isoformat() if token.HasField('expires_at') else None,
             'our_compute_invoked':False,'credential_values_output':False,'budget_caps_verified_by_api':False}
        if match:
            try:
                settings=await asyncio.wait_for(client._stub.WorkspaceSettings(empty_pb2.Empty()),timeout=10)
                out['workspace_settings']={'default_environment':settings.default_environment_name,'image_builder_version':settings.image_builder_version}
                out['workspace_settings_read']='PASS'
            except Exception as error:
                out['workspace_settings_read']='UNAVAILABLE'
                out['settings_error_type']=type(error).__name__
        return out
    finally:
        if client is not None:
            await client._close()
try:
    result=asyncio.run(asyncio.wait_for(inspect(),timeout=25))
except Exception as error:
    result={'authenticated':False,'error_type':type(error).__name__,'our_compute_invoked':False,'credential_values_output':False}
print(json.dumps(result,ensure_ascii=False))
