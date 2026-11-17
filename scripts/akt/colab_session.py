"""OAuth Colab lưu riêng trên D và đọc official MCP, không tạo compute."""
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
PRIVATE = ROOT / 'artifacts/akt/private/colab-session'
CLIENT_CONFIG = ROOT / 'artifacts/akt/private/drive-upload/client_secret.json'
ENDPOINT = 'https://colaboratory.googleapis.com/mcp'
COLAB_SCOPE = 'https://www.googleapis.com/auth/colaboratory'
SCOPES = ('openid', 'https://www.googleapis.com/auth/userinfo.email', COLAB_SCOPE)
ACCOUNT = 'honguyenminhsang2005@gmail.com'
READ_TOOLS = {'get_subscription', 'list_runtimes', 'list_runtime_specs', 'get_runtime'}


class ColabSessionError(RuntimeError):
    pass


def scope_set(value):
    if isinstance(value, str):
        value = value.split()
    if not isinstance(value, (list, tuple, set, frozenset)) or not all(isinstance(item, str) for item in value):
        raise ColabSessionError('OAUTH_ACTUAL_SCOPES_UNAVAILABLE')
    aliases = {'email': 'https://www.googleapis.com/auth/userinfo.email',
               'profile': 'https://www.googleapis.com/auth/userinfo.profile'}
    return {aliases.get(item, item) for item in value}


def required_grants(value):
    granted = scope_set(value)
    names = {'openid':'IDENTITY', 'https://www.googleapis.com/auth/userinfo.email':'EMAIL',
             COLAB_SCOPE:'COLAB_RUNTIME'}
    missing = [names[scope] for scope in SCOPES if scope not in granted]
    if missing:
        raise ColabSessionError('COLAB_PERMISSIONS_MISSING_' + '_'.join(missing))
    return granted


def edge_browser():
    """Chỉ mở Edge đã có trên Windows theo lựa chọn của người dùng."""
    import webbrowser
    candidates = (
        Path('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'),
        Path('C:/Program Files/Microsoft/Edge/Application/msedge.exe'))
    for executable in candidates:
        if executable.is_file():
            webbrowser.register('kltn-edge', None, webbrowser.BackgroundBrowser(str(executable)))
            return 'kltn-edge'
    raise ColabSessionError('EDGE_BROWSER_MISSING')


def private_path(path):
    path, base = Path(path).absolute(), PRIVATE.resolve()
    if not path.is_relative_to(base) or path.resolve() != path:
        raise ColabSessionError('PRIVATE_PATH_REJECTED')
    return path


def save_private(path, value):
    path = private_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        with temporary.open('x', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, sort_keys=True, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.chmod(0o600)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def save_credentials(path, credentials):
    actual = getattr(credentials, 'granted_scopes', None)
    if actual is None:
        actual = getattr(credentials, 'scopes', None)
    granted = required_grants(actual)
    info = json.loads(credentials.to_json())
    info['scopes'] = sorted(granted)
    save_private(path, info)


def refresh_credentials(credentials, request_factory=None):
    """Thử lại lỗi truyền tải hữu hạn, giữ nguyên quyền đã được cấp."""
    from google.auth.exceptions import TransportError
    from google.auth.transport.requests import Request
    request = (request_factory or Request)()
    def bounded_request(*args, **kwargs):
        kwargs['timeout'] = (5, 15)
        return request(*args, **kwargs)
    for attempt in range(3):
        try:
            credentials.refresh(bounded_request)
            return
        except TransportError:
            if attempt == 2:
                raise ColabSessionError('COLAB_AUTH_NETWORK_UNAVAILABLE') from None
            time.sleep(attempt+1)


def load_credentials(token_path, client_config=CLIENT_CONFIG, *, interactive=False,
                     credentials_type=None, flow_type=None, request_factory=None):
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    token_path = private_path(token_path)
    credentials_type = credentials_type or Credentials
    request_factory = request_factory or Request
    credentials = None
    if token_path.exists():
        credentials = credentials_type.from_authorized_user_file(str(token_path))
        if not credentials.has_scopes([COLAB_SCOPE]):
            credentials = None
    if credentials is not None and not credentials.valid and credentials.refresh_token:
        try:
            refresh_credentials(credentials, request_factory)
        except ColabSessionError:
            raise
        except Exception:
            if not interactive:
                raise ColabSessionError('LOGIN_REQUIRED_REFRESH_FAILED') from None
            credentials = None
    if credentials is None or not credentials.valid:
        if not interactive:
            raise ColabSessionError('LOGIN_REQUIRED')
        if not Path(client_config).is_file():
            raise ColabSessionError('DESKTOP_OAUTH_CLIENT_CONFIG_MISSING')
        if flow_type is None:
            from google_auth_oauthlib.flow import InstalledAppFlow
            flow_type = InstalledAppFlow
        flow = flow_type.from_client_secrets_file(str(client_config), scopes=SCOPES)
        try:
            credentials = flow.run_local_server(host='localhost', port=0, open_browser=True,
                browser=edge_browser(), timeout_seconds=1800,
                access_type='offline', prompt='consent',
                authorization_prompt_message='Trình duyệt Google đã mở để xác nhận quyền Colab.',
                success_message='Đã xác nhận quyền Colab. Có thể đóng tab này.')
        except Warning as warning:
            # oauthlib giữ response đã phân tích trên Warning trước khi gắn token.
            # Chỉ phục hồi nếu quyền thật đủ, không bỏ kiểm bằng biến relax scope.
            session = getattr(flow, 'oauth2session', None)
            token = getattr(warning, 'token', None)
            if not isinstance(token, dict):
                token = getattr(session, 'token', None)
            granted = required_grants(getattr(warning, 'new_scope', None))
            if (not isinstance(token, dict) or not token.get('access_token') or session is None
                    or scope_set(token.get('scope')) != granted):
                raise ColabSessionError('OAUTH_SCOPE_RESPONSE_UNAVAILABLE') from None
            session.token = dict(token)
            credentials = flow.credentials
        session = getattr(flow, 'oauth2session', None)
        token = getattr(session, 'token', {})
        actual = token.get('scope') if isinstance(token, dict) else None
        if actual is None:
            actual = getattr(credentials, 'granted_scopes', None)
        granted = required_grants(actual)
        if not credentials.refresh_token:
            raise ColabSessionError('PERSISTENT_COLAB_SCOPE_NOT_GRANTED')
        # Credentials.scopes của helper có thể chứa requested thay vì granted.
        # Lưu đúng quyền được cấp để has_scopes ở lần gọi sau phản ánh thực tế.
        info = json.loads(credentials.to_json())
        info['scopes'] = sorted(granted)
        credentials = Credentials.from_authorized_user_info(info)
    save_credentials(token_path, credentials)
    return credentials


def parse_response(response):
    if response.status_code != 200:
        raise ColabSessionError('COLAB_HTTP_' + str(response.status_code))
    text = response.text
    if len(text.encode('utf-8')) > 4 * 1024**2:
        raise ColabSessionError('COLAB_RESPONSE_TOO_LARGE')
    if 'text/event-stream' not in response.headers.get('Content-Type', ''):
        try:
            return json.loads(text)
        except (ValueError, TypeError):
            raise ColabSessionError('INVALID_COLAB_JSON') from None
    terminal = None
    for frame in text.replace('\r\n', '\n').split('\n\n'):
        data = '\n'.join(line[5:].lstrip() for line in frame.splitlines() if line.startswith('data:'))
        if data:
            try:
                message = json.loads(data)
            except ValueError:
                raise ColabSessionError('INVALID_COLAB_SSE_JSON') from None
            if isinstance(message, dict) and ('result' in message or 'error' in message):
                terminal = message
    if terminal is None:
        raise ColabSessionError('COLAB_SSE_TERMINAL_MISSING')
    return terminal


def public_result(value):
    """Loại token/URL proxy khỏi mọi output public của CLI."""
    if isinstance(value, dict):
        return {key: public_result(item) for key, item in value.items()
                if key not in {'connectionInfo', 'token', 'refresh_token', 'access_token', 'url'}}
    if isinstance(value, list):
        return [public_result(item) for item in value]
    return value


class ColabClient:
    def __init__(self, session, credentials, token_path, proxy_path):
        self.session, self.credentials = session, credentials
        self.token_path, self.proxy_path = private_path(token_path), private_path(proxy_path)
        self.sequence = 0

    def call(self, tool, arguments=None):
        if tool not in READ_TOOLS:
            raise ColabSessionError('COMPUTE_TOOL_NOT_ENABLED')
        self.sequence += 1
        body = dict(jsonrpc='2.0', id=self.sequence, method='tools/call',
                    params=dict(name=tool, arguments=arguments or {}))
        response = None
        try:
            response = self.session.post(ENDPOINT, json=body,
                headers={'Content-Type':'application/json','Accept':'application/json, text/event-stream'},
                timeout=(15,45), allow_redirects=False)
            message = parse_response(response)
            if message.get('error'):
                code = message['error'].get('code')
                safe = str(code) if type(code) is int else 'UNKNOWN'
                raise ColabSessionError('COLAB_RPC_ERROR_' + safe)
            if message.get('id') != self.sequence:
                raise ColabSessionError('COLAB_RPC_ID_MISMATCH')
            result = message.get('result', {})
            if result.get('isError'):
                raise ColabSessionError('COLAB_TOOL_ERROR')
            if 'structuredContent' in result:
                return result['structuredContent']
            for item in result.get('content', []):
                if item.get('type') == 'text':
                    try:
                        return json.loads(item['text'])
                    except ValueError:
                        continue
            raise ColabSessionError('COLAB_STRUCTURED_RESULT_MISSING')
        except ColabSessionError:
            raise
        except Exception as error:
            raise ColabSessionError('COLAB_TRANSPORT_' + type(error).__name__) from None
        finally:
            if response is not None:
                response.close()
            save_credentials(self.token_path, self.credentials)

    def runtime(self, name):
        if not re.fullmatch(r'runtimes/[A-Za-z0-9._-]{1,160}', name):
            raise ColabSessionError('INVALID_RUNTIME_NAME')
        cache = json.loads(self.proxy_path.read_text()) if self.proxy_path.exists() else {}
        if name in cache:
            expires = cache[name].get('connectionInfo', {}).get('expireTime')
            if expires:
                try:
                    limit = datetime.fromisoformat(expires.replace('Z', '+00:00'))
                    if limit > datetime.now(timezone.utc) + timedelta(minutes=5):
                        return cache[name]
                except (ValueError, TypeError):
                    pass
        result = self.call('get_runtime', {'name': name})
        if result.get('name') != name:
            raise ColabSessionError('RUNTIME_BINDING_MISMATCH')
        cache[name] = result
        save_private(self.proxy_path, cache)
        return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('login','subscription','runtimes','specs','runtime'))
    parser.add_argument('name', nargs='?')
    parser.add_argument('--client-config', type=Path, default=CLIENT_CONFIG)
    args = parser.parse_args()
    credentials = load_credentials(PRIVATE/'credentials.json', args.client_config, interactive=args.command == 'login')
    from google.auth.transport.requests import AuthorizedSession
    with AuthorizedSession(credentials) as session:
        identity = session.get('https://www.googleapis.com/oauth2/v3/userinfo', timeout=30, allow_redirects=False)
        if identity.status_code != 200 or identity.json().get('email') != ACCOUNT:
            raise ColabSessionError('COLAB_ACCOUNT_MISMATCH')
        if args.command == 'login':
            result = dict(status='PERSISTENT_COLAB_OAUTH_SAVED', account=ACCOUNT, scope=COLAB_SCOPE,
                          runtime_created=False, code_executed=False)
        else:
            client = ColabClient(session, credentials, PRIVATE/'credentials.json', PRIVATE/'runtime-proxies.json')
            result = client.runtime(args.name or '') if args.command == 'runtime' else client.call(
                {'subscription':'get_subscription','runtimes':'list_runtimes','specs':'list_runtime_specs'}[args.command])
        print(json.dumps(public_result(result), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        message = str(error) if isinstance(error, ColabSessionError) else type(error).__name__
        print(json.dumps(dict(status='COLAB_SESSION_STOPPED', reason=message)))
        raise SystemExit(1)
