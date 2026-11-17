"""CPU Colab miễn phí, session riêng và request tiếp tục có pin trên D.

Chỉ chạy khi caller gọi CLI phase rõ ràng. Không giữ sống giả hoặc dùng GPU.
"""
import hashlib
import json
from pathlib import Path
import re
import uuid

try:
    from . import colab_session as auth
except ImportError:
    import colab_session as auth

ROOT = Path(__file__).resolve().parents[2]
SPEC = {'variant':'VARIANT_CPU','accelerator':'NONE','shape':'SHAPE_STANDARD'}


def _need(condition, message):
    if not condition:
        raise auth.ColabSessionError(message)


def _read(path):
    path = auth.private_path(path)
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {'version':1,'executions':{}}


def _mutate(client, tool, arguments):
    _need(tool in {'create_runtime','create_session','execute_code'}, 'TOOL_NOT_ADMITTED')
    client.sequence += 1
    response = None
    try:
        response = client.session.post(auth.ENDPOINT,
            json=dict(jsonrpc='2.0',id=client.sequence,method='tools/call',
                      params=dict(name=tool,arguments=arguments)),
            headers={'Content-Type':'application/json','Accept':'application/json, text/event-stream'},
            timeout=(15,650), allow_redirects=False)
        message = auth.parse_response(response)
        _need(message.get('id') == client.sequence, 'COLAB_RPC_ID_MISMATCH')
        if message.get('error'):
            code = message['error'].get('code')
            raise auth.ColabSessionError('COLAB_RPC_ERROR_' + (str(code) if type(code) is int else 'UNKNOWN'))
        result = message.get('result', {})
        _need(not result.get('isError'), 'COLAB_TOOL_ERROR')
        if 'structuredContent' in result:
            return result['structuredContent']
        for entry in result.get('content', []):
            if entry.get('type') == 'text':
                try:
                    return json.loads(entry['text'])
                except ValueError:
                    continue
        raise auth.ColabSessionError('COLAB_STRUCTURED_RESULT_MISSING')
    except auth.ColabSessionError:
        raise
    except Exception as error:
        raise auth.ColabSessionError('COLAB_TRANSPORT_' + type(error).__name__) from None
    finally:
        if response is not None:
            response.close()
        auth.save_credentials(client.token_path, client.credentials)


def _send(client, path, state, request):
    _validate_request(request)
    if request['status'] == 'COMPLETE':
        _validate_result(request, request['result'])
        return request['result']
    _need(request['status'] in {'PENDING','UNCERTAIN'}, 'TERMINAL_REQUEST_REQUIRES_REVIEW')
    auth.save_private(path, state)
    try:
        result = _mutate(client, request['tool'], request['arguments'])
        _validate_result(request, result)
    except auth.ColabSessionError as error:
        retryable = str(error) in {'COLAB_RPC_ERROR_4','COLAB_RPC_ERROR_14',
            'COLAB_TRANSPORT_ReadTimeout','COLAB_TRANSPORT_Timeout','COLAB_HTTP_504'}
        request.update(status='UNCERTAIN' if retryable else 'FAILED', reason=str(error))
        auth.save_private(path, state)
        raise
    request.update(status='COMPLETE', result=result)
    auth.save_private(path, state)
    return result


def _validate_request(request):
    arguments, tool = request['arguments'], request['tool']
    if tool == 'create_runtime':
        _need(set(arguments) == {'runtime','requestId'} and arguments['runtime'] == {'runtimeSpec':SPEC}, 'CPU_REQUEST_CHANGED')
        identity = arguments['requestId']
    elif tool == 'create_session':
        _need(set(arguments) == {'parent','sessionId'} and _runtime_name(arguments['parent'])
              and re.fullmatch(r'kltn-[0-9a-f]{32}', arguments['sessionId']), 'OWN_SESSION_REQUEST_CHANGED')
        return
    elif tool == 'execute_code':
        _need(set(arguments) == {'code','session','executionId'}
              and isinstance(arguments['code'], str) and len(arguments['code'].encode('utf-8')) <= 256*1024
              and re.fullmatch(r'runtimes/[A-Za-z0-9._-]{1,160}/sessions/kltn-[0-9a-f]{32}', arguments['session']), 'EXECUTION_REQUEST_CHANGED')
        identity = arguments['executionId']
    else:
        raise auth.ColabSessionError('TOOL_NOT_ADMITTED')
    try:
        parsed = uuid.UUID(identity)
    except (ValueError, TypeError, AttributeError):
        raise auth.ColabSessionError('REQUEST_UUID4_REQUIRED') from None
    _need(parsed.version == 4 and str(parsed) == identity, 'REQUEST_UUID4_REQUIRED')


def _validate_result(request, result):
    arguments = request['arguments']
    if request['tool'] == 'create_runtime':
        _need(_runtime_name(result.get('name')) and result.get('runtimeSpec') == SPEC, 'CPU_RESULT_NOT_ADMITTED')
    elif request['tool'] == 'create_session':
        _need(result.get('name') == arguments['parent']+'/sessions/'+arguments['sessionId'], 'OWN_SESSION_RESULT_CHANGED')
    else:
        _need(result.get('session') == arguments['session']
              and result.get('executionId') == arguments['executionId'], 'EXECUTION_RESULT_BINDING_CHANGED')


def _free_gate(client):
    _need(client.call('get_subscription').get('tier') == 'SUBSCRIPTION_TIER_FREE', 'FREE_SUBSCRIPTION_REQUIRED')
    specs = client.call('list_runtime_specs').get('runtimeSpecs', [])
    _need(any(row.get('key') == SPEC and row.get('eligible') is True for row in specs), 'ELIGIBLE_STANDARD_FREE_CPU_REQUIRED')


def _runtime_name(value):
    return isinstance(value, str) and re.fullmatch(r'runtimes/[A-Za-z0-9._-]{1,160}', value)


def ensure_cpu_runtime(client, state_path):
    _free_gate(client)
    state = _read(state_path)
    if state.get('runtime'):
        saved = state['runtime']
        _need(_runtime_name(saved['name']), 'INVALID_RUNTIME_NAME')
        actual = client.call('get_runtime', {'name':saved['name']})
        _need(actual.get('name') == saved['name'] and actual.get('runtimeSpec') == SPEC, 'CPU_RUNTIME_CHANGED')
        return saved
    if state.get('runtime_request'):
        pending = state['runtime_request']
        _need(pending['tool'] == 'create_runtime', 'CPU_REQUEST_CHANGED')
        result = _send(client, state_path, state, pending)
        owned = True
    else:
        runtimes = client.call('list_runtimes').get('runtimes', [])
        candidates = sorted((r for r in runtimes if r.get('runtimeSpec') == SPEC and _runtime_name(r.get('name'))), key=lambda r:r['name'])
        if candidates:
            result, owned = candidates[0], False
        else:
            request = dict(tool='create_runtime', status='PENDING', arguments={
                'runtime':{'runtimeSpec':dict(SPEC)}, 'requestId':str(uuid.uuid4())})
            state['runtime_request'] = request
            result = _send(client, state_path, state, request)
            owned = True
    _need(_runtime_name(result.get('name')) and result.get('runtimeSpec') == SPEC, 'CPU_RESULT_NOT_ADMITTED')
    state['runtime'] = dict(name=result['name'],runtimeSpec=dict(SPEC),owned=owned)
    auth.save_private(state_path, state)
    return state['runtime']


def ensure_session(client, state_path):
    runtime = ensure_cpu_runtime(client, state_path)
    state = _read(state_path)
    if not state.get('session_request'):
        state['session_request'] = dict(tool='create_session',status='PENDING',arguments={
            'parent':runtime['name'],'sessionId':'kltn-'+uuid.uuid4().hex})
    request = state['session_request']
    _need(request['tool'] == 'create_session' and request['arguments']['parent'] == runtime['name']
          and re.fullmatch(r'kltn-[0-9a-f]{32}', request['arguments']['sessionId']), 'OWN_SESSION_BINDING_CHANGED')
    result = _send(client, state_path, state, request)
    expected = runtime['name']+'/sessions/'+request['arguments']['sessionId']
    _need(result.get('name') == expected, 'OWN_SESSION_RESULT_CHANGED')
    return expected


def _summary(phase, execution):
    result = execution['result']
    return dict(phase=phase,status='COMPLETE',source_sha256=execution['source_sha256'],
                execution_id=execution['arguments']['executionId'],
                execution_error=bool(result.get('executionError')),
                output_truncated=bool(result.get('outputTruncated')),
                output_stored_privately=True)


def execute_script(client, state_path, script, expected_sha256, phase):
    script = Path(script).absolute()
    allowed = (ROOT/'scripts/akt').resolve(strict=True)
    _need(script.suffix == '.py' and script.is_relative_to(allowed)
          and script.resolve(strict=True) == script and script.stat().st_size <= 256*1024,
          'TRUSTED_REPOSITORY_SCRIPT_REQUIRED')
    _need(re.fullmatch(r'[a-z0-9][a-z0-9._-]{0,62}', phase), 'EXPLICIT_PHASE_REQUIRED')
    data = script.read_bytes()
    _need(hashlib.sha256(data).hexdigest() == expected_sha256, 'SCRIPT_SHA_MISMATCH')
    code = data.decode('utf-8')
    compile(code, str(script), 'exec')
    state = _read(state_path)
    existing = state['executions'].get(phase)
    if existing:
        _need(existing['tool'] == 'execute_code' and existing['source_sha256'] == expected_sha256
              and existing['arguments']['code'] == code, 'PHASE_IDENTITY_CHANGED')
        if existing['status'] == 'COMPLETE':
            _validate_request(existing)
            _validate_result(existing, existing['result'])
            return _summary(phase, existing)
    session = ensure_session(client, state_path)
    state = _read(state_path)
    if phase not in state['executions']:
        state['executions'][phase] = dict(tool='execute_code',status='PENDING',
            source_sha256=expected_sha256,arguments=dict(code=code,session=session,executionId=str(uuid.uuid4())))
    execution = state['executions'][phase]
    _need(execution['arguments']['session'] == session, 'EXECUTION_SESSION_CHANGED')
    result = _send(client, state_path, state, execution)
    _need(result.get('session') == session and result.get('executionId') == execution['arguments']['executionId'], 'EXECUTION_RESULT_BINDING_CHANGED')
    return _summary(phase, execution)


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('runtime','session','execute'))
    parser.add_argument('--script', type=Path)
    parser.add_argument('--sha256')
    parser.add_argument('--phase')
    args = parser.parse_args()
    credentials = auth.load_credentials(auth.PRIVATE/'credentials.json')
    from google.auth.transport.requests import AuthorizedSession
    try:
        from .drive_resumable_upload import single_writer
    except ImportError:
        from drive_resumable_upload import single_writer
    with single_writer(auth.PRIVATE/'cpu-execution.lock'), AuthorizedSession(credentials) as session:
        identity = session.get('https://openidconnect.googleapis.com/v1/userinfo',timeout=30,allow_redirects=False)
        _need(identity.status_code == 200 and identity.json().get('email') == auth.ACCOUNT, 'COLAB_ACCOUNT_MISMATCH')
        client = auth.ColabClient(session,credentials,auth.PRIVATE/'credentials.json',auth.PRIVATE/'runtime-proxies.json')
        path = auth.PRIVATE/'cpu-execution.json'
        if args.command == 'runtime':
            result = ensure_cpu_runtime(client,path)
        elif args.command == 'session':
            result = dict(session=ensure_session(client,path))
        else:
            _need(args.script is not None and args.sha256 and args.phase, 'EXPLICIT_SCRIPT_SHA_PHASE_REQUIRED')
            result = execute_script(client,path,args.script,args.sha256,args.phase)
        print(json.dumps(auth.public_result(result),ensure_ascii=False,indent=2))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        reason = str(error) if isinstance(error, auth.ColabSessionError) else type(error).__name__
        print(json.dumps(dict(status='CPU_EXECUTION_STOPPED',reason=reason)))
        raise SystemExit(1)
