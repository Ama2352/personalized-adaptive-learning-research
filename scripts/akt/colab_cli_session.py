"""Transport consumer của CLI Google cho CPU chuẩn, không cần bật Cloud API."""
from datetime import datetime, timedelta, timezone
import json
import hashlib
import math
from pathlib import Path
import re
import time
import uuid
from urllib.parse import urlsplit

try:
    from . import colab_session as auth
except ImportError:
    import colab_session as auth

DOMAIN = 'https://colab.research.google.com/tun/m/'
HEADERS = {'Accept':'application/json','X-Colab-Client-Agent':'colab-cli'}


def need(value, message):
    if not value:
        raise auth.ColabSessionError(message)


def read_json(session, method, url, **kwargs):
    import requests
    response = None
    try:
        headers = dict(HEADERS, **kwargs.pop('headers', {}))
        attempts = 3 if method == 'GET' else 1
        for attempt in range(attempts):
            try:
                response = session.request(method,url,headers=headers,timeout=(15,120),allow_redirects=False,**kwargs)
                break
            except (requests.ConnectionError, requests.Timeout) as error:
                if isinstance(error, requests.exceptions.SSLError) or attempt == attempts-1:
                    raise
                time.sleep(attempt+1)
        need(response.status_code in (200,201), 'COLAB_CLI_HTTP_'+str(response.status_code))
        text = response.text
        need(len(text.encode()) <= 4*1024**2, 'COLAB_CLI_RESPONSE_TOO_LARGE')
        return json.loads(text[5:] if text.startswith(")]}'\n") else text)
    except auth.ColabSessionError:
        raise
    except Exception as error:
        raise auth.ColabSessionError('COLAB_CLI_TRANSPORT_'+type(error).__name__) from None
    finally:
        if response is not None:
            response.close()


def _free_usage(session):
    usage = read_json(session,'GET',DOMAIN+'ccu-info',params={'authuser':'0'})
    rate = usage.get('consumptionRateHourly')
    quota = usage.get('freeCcuQuotaInfo',{}).get('remainingTokens','0')
    remaining = int(quota) if isinstance(quota,(str,int)) and str(quota).isdigit() else 0
    # consumptionRateHourly là compute units, không phải số tiền phải trả.
    need(usage.get('currentBalance') == 0 and type(rate) in (int,float)
         and math.isfinite(rate) and rate >= 0 and (rate == 0 or remaining > 0),
         'FREE_CPU_QUOTA_WITHOUT_PAID_BALANCE_REQUIRED')
    return usage


def _cpu(row):
    return (row.get('accelerator') == 'NONE' and row.get('variant') == 0
            and row.get('machineShape',0) == 0
            and isinstance(row.get('endpoint'),str)
            and re.fullmatch(r'[A-Za-z0-9._-]{1,250}',row['endpoint']))


def ensure_cpu_assignment(session, state_path):
    """Ghim own nbh trước GET/POST, đối chiếu CPU và quota miễn phí."""
    state_path = auth.private_path(state_path)
    _free_usage(session)
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    rows = read_json(session,'GET',DOMAIN+'assignments',params={'authuser':'0'})['assignments']
    if state.get('endpoint'):
        matches = [r for r in rows if r.get('endpoint') == state['endpoint']]
        need(len(matches) == 1 and _cpu(matches[0]), 'OWN_CPU_ASSIGNMENT_UNAVAILABLE')
        result = matches[0]
    else:
        if not state.get('assign_params'):
            identifier = str(uuid.uuid4()).replace('-','_') + '.'*8
            state['assign_params'] = {'nbh':identifier,'variant':'DEFAULT','accelerator':'NONE','authuser':'0'}
            auth.save_private(state_path,state)
        params = state['assign_params']
        need(set(params) == {'nbh','variant','accelerator','authuser'}
             and params['variant'] == 'DEFAULT' and params['accelerator'] == 'NONE'
             and params['authuser'] == '0'
             and re.fullmatch(r'[0-9a-f_]{36}\.{8}',params['nbh']), 'CPU_ASSIGNMENT_REQUEST_CHANGED')
        # GET với cùng nbh đối chiếu kết quả POST chưa rõ trước khi gửi lại.
        admission = read_json(session,'GET',DOMAIN+'assign',params=params)
        if admission.get('endpoint'):
            assigned = admission
        else:
            need(isinstance(admission.get('acc'), str) and admission['acc'].upper() == 'NONE'
                 and admission.get('variant') == 'DEFAULT'
                 and admission.get('nbh') == params['nbh'] and admission.get('token'), 'CPU_ASSIGNMENT_ADMISSION_CHANGED')
            state['status'] = 'ASSIGN_POST_PENDING'
            auth.save_private(state_path,state)
            assigned = read_json(session,'POST',DOMAIN+'assign',params=params,
                                 headers={'X-Goog-Colab-Token':admission['token']})
        need(isinstance(assigned.get('endpoint'),str), 'CPU_ASSIGNMENT_RESULT_MISSING')
        state['endpoint'] = assigned['endpoint']
        auth.save_private(state_path,state)
        rows = read_json(session,'GET',DOMAIN+'assignments',params={'authuser':'0'})['assignments']
        matches = [row for row in rows if row.get('endpoint') == state['endpoint']]
        need(len(matches) == 1 and _cpu(matches[0]), 'CPU_ASSIGNMENT_NOT_VERIFIED')
        result = matches[0]
    _free_usage(session)
    proxy = result.get('runtimeProxyInfo',{})
    parsed = urlsplit(proxy.get('url',''))
    need(parsed.scheme == 'https' and parsed.hostname and not parsed.username
         and not parsed.password and proxy.get('token')
         and type(proxy.get('tokenExpiresInSeconds')) is int and proxy['tokenExpiresInSeconds'] > 0,
         'CPU_PROXY_RESPONSE_REJECTED')
    state.update(status='CPU_ASSIGNMENT_VERIFIED',assignment=result,
        proxy_expires_at=(datetime.now(timezone.utc)+timedelta(seconds=proxy['tokenExpiresInSeconds'])).isoformat())
    auth.save_private(state_path,state)
    return result


def _proxy_request(session, assignment, method, path, **kwargs):
    proxy = assignment['runtimeProxyInfo']
    need(path.startswith(('api/sessions','api/contents/')) and '..' not in path
         and method in ('GET','POST','PUT'), 'OWN_JUPYTER_ROUTE_REQUIRED')
    return read_json(session,method,proxy['url'].rstrip('/')+'/'+path,
        headers={'X-Colab-Runtime-Proxy-Token':proxy['token'],
                 'Authorization':'Bearer '+proxy['token']},**kwargs)


def ensure_kernel(session, state_path, *, proxy_session=None):
    """Session notebook UUID riêng, tìm lại theo path trước POST kernel."""
    assignment = ensure_cpu_assignment(session,state_path)
    state = json.loads(Path(state_path).read_text()) if Path(state_path).exists() else {}
    if not state.get('kernel_request'):
        identity = uuid.uuid4().hex
        state['kernel_request'] = dict(path='content/kltn-agent-'+identity+'.ipynb',name='kltn-agent-'+identity,
                                       wire_session_id=str(uuid.uuid4()))
        auth.save_private(state_path,state)
    request = state['kernel_request']
    need(re.fullmatch(r'content/kltn-agent-[0-9a-f]{32}\.ipynb',request['path'])
         and request['name'] == Path(request['path']).stem, 'OWN_NOTEBOOK_REQUEST_CHANGED')
    owned_proxy = proxy_session is None
    if owned_proxy:
        import requests
        proxy_session = requests.Session()
    try:
        sessions = _proxy_request(proxy_session,assignment,'GET','api/sessions')
        matches = [row for row in sessions if row.get('path') == request['path']]
        need(len(matches) <= 1, 'OWN_SESSION_AMBIGUOUS')
        if matches:
            result = matches[0]
        else:
            need(not state.get('kernel_post_pending'), 'KERNEL_CREATION_UNCERTAIN_RECONCILE_ONLY')
            notebook = dict(nbformat=4,nbformat_minor=5,metadata={},cells=[])
            _proxy_request(proxy_session,assignment,'PUT','api/contents/'+request['path'],
                json=dict(type='notebook',format='json',content=notebook))
            state['kernel_post_pending'] = True
            auth.save_private(state_path,state)
            result = _proxy_request(proxy_session,assignment,'POST','api/sessions',
                json=dict(path=request['path'],name=request['name'],type='notebook',kernel={'name':'python3'}))
        need(result.get('path') == request['path'] and result.get('id')
             and result.get('kernel',{}).get('name') == 'python3' and result['kernel'].get('id'), 'OWN_KERNEL_BINDING_CHANGED')
        kernel = dict(session_id=result['id'],kernel_id=result['kernel']['id'],path=request['path'],
                      wire_session_id=request['wire_session_id'])
        if state.get('kernel'):
            need(state['kernel'] == kernel, 'OWN_KERNEL_REPLACED')
        state.update(kernel=kernel,kernel_post_pending=False)
        auth.save_private(state_path,state)
        return assignment,kernel
    finally:
        if owned_proxy:
            proxy_session.close()


def _close_kernel_transport(client):
    if client is None:
        return
    try:
        wire = client._manager.client
        try:
            wire.stop_channels()
        finally:
            if wire.kernel_socket:
                wire.kernel_socket.close()
    except Exception:
        pass


def _connect_kernel(assignment, kernel, kernel_factory=None):
    import logging
    for name in ('jupyter_kernel_client','websocket'):
        logging.getLogger(name).setLevel(logging.CRITICAL+1)
    from jupyter_kernel_client import JupyterSubprotocol
    if kernel_factory is None:
        from jupyter_kernel_client import JupyterKernelClient
        kernel_factory = JupyterKernelClient
    proxy = assignment['runtimeProxyInfo']
    client = None
    import requests
    for attempt in range(3):
        try:
            client = kernel_factory(server_url=proxy['url'],token=proxy['token'],kernel_id=kernel['kernel_id'],
                client_kwargs={'session':kernel['wire_session_id'],'subprotocol':JupyterSubprotocol.DEFAULT,
                              'extra_params':{'colab-runtime-proxy-token':proxy['token']}},
                headers={'X-Colab-Client-Agent':'colab-cli','X-Colab-Runtime-Proxy-Token':proxy['token']})
            client._own_kernel = False
            client.start(timeout=30)
            return client
        except (requests.ConnectTimeout,requests.ReadTimeout):
            _close_kernel_transport(client)
            client = None
            if attempt == 2:
                raise
            time.sleep(2**(attempt+1))
        except Exception:
            _close_kernel_transport(client)
            raise


def discover_cpu(session, state_path, *, kernel_factory=None):
    """Một lượt đọc Python/RAM, đóng socket nhưng giữ own kernel/session."""
    assignment,kernel = ensure_kernel(session,state_path)
    client = None
    try:
        client = _connect_kernel(assignment,kernel,kernel_factory)
        code = ("import json,sys\n"
                "_mem={r.split(':')[0]:r.split(':')[1].strip() for r in open('/proc/meminfo')}\n"
                "print(json.dumps({'python':sys.version,'executable':sys.executable,"
                "'available_memory_bytes':int(_mem['MemAvailable'].split()[0])*1024}))")
        result = client.execute(code,allow_stdin=False,timeout=60)
        need(result.get('status') == 'ok', 'CPU_DISCOVERY_EXECUTION_FAILED')
        text = ''.join(row.get('text','') for row in result.get('outputs',[]) if row.get('output_type') == 'stream')
        data = json.loads(text.strip())
        need(set(data) == {'python','executable','available_memory_bytes'}, 'CPU_DISCOVERY_SCHEMA_CHANGED')
        return dict(status='CPU_KERNEL_DISCOVERY_COMPLETE',endpoint=assignment['endpoint'],**data)
    except auth.ColabSessionError:
        raise
    except Exception as error:
        raise auth.ColabSessionError('CPU_DISCOVERY_'+type(error).__name__) from None
    finally:
        _close_kernel_transport(client)


def execute_phase(session, state_path, script, expected_sha256, phase, *, timeout=3600):
    """Chạy một file tin cậy, không gửi lại nếu WS mất sau lúc gửi code."""
    script = Path(script).absolute()
    allowed_roots = (auth.ROOT/'scripts/akt',
                     auth.ROOT/'research_tracking/runs/junyi-calibration-real-20261117-01')
    need(any(script.is_relative_to(root.resolve()) for root in allowed_roots)
         and script.resolve(strict=True) == script
         and script.suffix == '.py' and script.stat().st_size <= 256*1024, 'TRUSTED_PHASE_FILE_REQUIRED')
    need(re.fullmatch(r'[a-z0-9][a-z0-9._-]{0,62}',phase), 'EXPLICIT_PHASE_REQUIRED')
    need(type(timeout) in (int,float) and math.isfinite(timeout) and 0 < timeout <= 10860,
         'BOUNDED_PHASE_TIMEOUT_REQUIRED')
    data = script.read_bytes()
    need(hashlib.sha256(data).hexdigest() == expected_sha256, 'PHASE_SOURCE_SHA_MISMATCH')
    source = data.decode('utf-8')
    compile(source,str(script),'exec')
    state_path = auth.private_path(state_path)
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    phases = state.get('phases',{})
    if phase in phases:
        saved = phases[phase]
        need(saved['source_sha256'] == expected_sha256, 'PHASE_IDENTITY_CHANGED')
        need(saved['status'] == 'COMPLETE', 'PHASE_ALREADY_SENT_CHECK_REMOTE_STATUS')
        return saved['summary']
    assignment,kernel = ensure_kernel(session,state_path)
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    identity = str(uuid.uuid4())
    marker = '/content/kltn-agent-phase-'+identity+'.json'
    saved = dict(phase_id=identity,source_sha256=expected_sha256,script=script.relative_to(auth.ROOT).as_posix(),
        kernel_id=kernel['kernel_id'],remote_status_path=marker,status='RUNNING_OR_UNCERTAIN')
    state.setdefault('phases',{})[phase] = saved
    auth.save_private(state_path,state)
    code = ("import json as _kltn_json, os as _kltn_os\nfrom pathlib import Path as _KltnPath\n"
        f"_kltn_marker=_KltnPath({marker!r})\n"
        "def _kltn_write(_status):\n"
        "    _tmp=_kltn_marker.with_suffix('.tmp')\n"
        f"    _payload=dict(status=_status,pid=_kltn_os.getpid(),phase={phase!r},source_sha256={expected_sha256!r})\n"
        "    _tmp.write_text(_kltn_json.dumps(_payload))\n"
        "    _kltn_os.replace(_tmp,_kltn_marker)\n"
        "_kltn_write('RUNNING')\ntry:\n"
        f"    exec(compile({source!r},{str(script)!r},'exec'),globals())\n"
        "except BaseException:\n    _kltn_write('ERROR')\n    raise\n"
        "else:\n    _kltn_write('COMPLETE')\n")
    client = None
    try:
        client = _connect_kernel(assignment,kernel)
        result = client.execute(code,allow_stdin=False,timeout=timeout)
        need(len(json.dumps(result).encode()) <= 4*1024**2, 'PHASE_OUTPUT_PRIVATE_LIMIT_EXCEEDED')
        summary = dict(phase=phase,phase_id=identity,status='COMPLETE',success=result.get('status') == 'ok',
                       source_sha256=expected_sha256,remote_status_path=marker,output_stored_privately=True)
        saved.update(status='COMPLETE',result=result,summary=summary)
        auth.save_private(state_path,state)
        return summary
    except Exception as error:
        saved.update(status='UNCERTAIN',error_type=type(error).__name__)
        auth.save_private(state_path,state)
        raise auth.ColabSessionError('PHASE_UNCERTAIN_CHECK_REMOTE_STATUS') from None
    finally:
        _close_kernel_transport(client)


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('cpu','status','kernel','discover','execute'))
    parser.add_argument('--script',type=Path)
    parser.add_argument('--sha256')
    parser.add_argument('--phase')
    parser.add_argument('--timeout-seconds',type=int,default=10860)
    args = parser.parse_args()
    credentials = auth.load_credentials(auth.PRIVATE/'credentials.json')
    from google.auth.transport.requests import AuthorizedSession
    try:
        from .drive_resumable_upload import single_writer
    except ImportError:
        from drive_resumable_upload import single_writer
    with single_writer(auth.PRIVATE/'cli-session.lock'), AuthorizedSession(credentials) as session:
        who = session.get('https://www.googleapis.com/oauth2/v3/userinfo',timeout=30,allow_redirects=False)
        need(who.status_code == 200 and who.json().get('email') == auth.ACCOUNT, 'COLAB_ACCOUNT_MISMATCH')
        try:
            if args.command == 'cpu':
                result = ensure_cpu_assignment(session,auth.PRIVATE/'cli-runtime.json')
            elif args.command == 'kernel':
                _,result = ensure_kernel(session,auth.PRIVATE/'cli-runtime.json')
            elif args.command == 'discover':
                result = discover_cpu(session,auth.PRIVATE/'cli-runtime.json')
            elif args.command == 'execute':
                need(args.script and args.sha256 and args.phase, 'EXPLICIT_SCRIPT_SHA_PHASE_REQUIRED')
                result = execute_phase(session,auth.PRIVATE/'cli-runtime.json',args.script,args.sha256,args.phase,
                                       timeout=args.timeout_seconds)
            else:
                result = read_json(session,'GET',DOMAIN+'assignments',params={'authuser':'0'})
        finally:
            auth.save_credentials(auth.PRIVATE/'credentials.json',credentials)
        print(json.dumps(auth.public_result(result),ensure_ascii=False,indent=2))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        reason = str(error) if isinstance(error,auth.ColabSessionError) else type(error).__name__
        print(json.dumps(dict(status='COLAB_CLI_STOPPED',reason=reason)))
        raise SystemExit(1)
