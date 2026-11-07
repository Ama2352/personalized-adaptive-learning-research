"""Client terminal cho Colab MCP chính thức, chạy trong .venv của KLTN.

Chỉ mở bridge localhost và gọi tools theo yêu cầu JSON qua stdin. Không tự
cấp runtime/GPU, chạy notebook, cài package remote hoặc dùng Modal khi khởi động.
Nonce kết nối chỉ nằm trong bộ nhớ và tab Google, không in ra stdout.
"""
from __future__ import annotations

import argparse
import asyncio
from contextlib import AsyncExitStack
import dataclasses
import json
import logging
from pathlib import Path
import re
import sys
import threading
import time
import uuid
import webbrowser

ROOT = Path(__file__).resolve().parents[1]
REQUESTS = ROOT / 'artifacts/akt/colab/requests'
PRIVATE = ROOT / 'artifacts/akt/private/colab-bridge'


def json_value(value):
    if hasattr(value, 'model_dump'):
        return value.model_dump(mode='json', by_alias=True)
    if dataclasses.is_dataclass(value):
        return {field.name: json_value(getattr(value, field.name)) for field in dataclasses.fields(value)}
    if isinstance(value, dict):
        return {str(key): json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_value(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def request_path(name):
    path = Path(name).resolve()
    if not path.is_relative_to(REQUESTS.resolve()) or path.suffix != '.json' or path.is_symlink():
        raise ValueError('args_file phải là JSON dưới artifacts/akt/colab/requests')
    if path.stat().st_size > 2 * 1024 * 1024:
        raise ValueError('request vượt2MiB')
    return path


def runtime_mutation(name):
    """Không tự provision/delete/purchase từ client notebook này."""
    return bool(re.search(r'(create|allocate|purchase|delete|new).*(runtime|server|billing|credits)', name, re.I))


async def main(args):
    if Path(sys.prefix).resolve() != (ROOT / '.venv').resolve():
        raise ValueError('Dùng .venv của KLTN')
    from fastmcp import FastMCP, Client
    from colab_mcp.session import ColabSessionProxy, INJECTED_TOOL_NAME
    from colab_mcp.websocket_server import COLAB, SCRATCH_PATH

    directory = PRIVATE / ('session-' + uuid.uuid4().hex)
    directory.mkdir(parents=True)
    REQUESTS.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=directory/'private-server.log', level=logging.WARNING)
    session = ColabSessionProxy()
    opened = 0
    deadline = time.monotonic() + args.ttl_seconds
    queue = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def emit(value):
        # Lọc nonce của bridge khỏi mọi output/log quản lý của client.
        text = json.dumps(json_value(value), ensure_ascii=False, allow_nan=False)
        if session.wss is not None:
            text = text.replace(session.wss.token, '[REDACTED]')
        print(text, flush=True)

    def reader():
        for line in sys.stdin:
            try:
                loop.call_soon_threadsafe(queue.put_nowait, line)
            except RuntimeError:
                return
        try:
            loop.call_soon_threadsafe(queue.put_nowait, None)
        except RuntimeError:
            pass

    async with AsyncExitStack() as stack:
        await session.start_proxy_server()
        stack.push_async_callback(session.cleanup)
        server = FastMCP('KLTNOfficialColabClient')
        server.mount(session.proxy_server)
        for middleware in session.middleware:
            server.add_middleware(middleware)
        client = await stack.enter_async_context(Client(server))
        proxy = session.middleware[0].proxy_client

        def status():
            value = {'event':'status', 'connected':proxy.is_connected(),
                     'websocket_live':session.wss.connection_live.is_set(),
                     'local_port':session.wss.port, 'directory':str(directory.relative_to(ROOT)),
                     'seconds_remaining':max(0, int(deadline-time.monotonic())),
                     'scope':'Local official MCP bridge; no automatic GPU/model execution'}
            (PRIVATE/'current.json').write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')
            return value

        def open_browser():
            nonlocal opened
            if opened >= 2:
                raise ValueError('Đã mở tab2lần; không retry browser tự động')
            # Cùng URL/template với tool của Google; mở không-block để không hủy
            # task MCP proxy nếu người dùng cần hơn60s để xác nhận trong browser.
            url = f'{COLAB}{SCRATCH_PATH}#mcpProxyToken={session.wss.token}&mcpProxyPort={session.wss.port}'
            opened += 1
            return {'event':'browser_open', 'opened':bool(webbrowser.open_new(url)),
                    'note':'Tab Google chính thức; xác nhận kết nối nếu được hỏi; URL nonce không được log'}

        emit({**status(), 'event':'ready'})
        if args.open_browser:
            emit(open_browser())
        threading.Thread(target=reader, daemon=True).start()
        previous = proxy.is_connected()
        while time.monotonic() < deadline:
            connected = proxy.is_connected()
            if connected != previous:
                emit(status())
                previous = connected
            try:
                line = await asyncio.wait_for(queue.get(), timeout=min(2, max(.01, deadline-time.monotonic())))
            except asyncio.TimeoutError:
                continue
            if line is None:
                break
            try:
                command = json.loads(line)
                action = command.get('action')
                if action == 'close':
                    break
                if action == 'status':
                    emit(status())
                elif action == 'open':
                    emit(open_browser())
                elif action == 'list':
                    tools = await asyncio.wait_for(client.list_tools(), timeout=20)
                    emit({'event':'tools', 'connected':proxy.is_connected(), 'tools':tools})
                elif action == 'call':
                    if not proxy.is_connected():
                        raise ValueError('Chưa có frontend Colab kết nối; không gọi remote tool')
                    name = command['name']
                    if name == INJECTED_TOOL_NAME or runtime_mutation(name):
                        raise ValueError('Không dùng tool mở bridge/cấp hoặc xóa runtime từ action call')
                    arguments = json.loads(request_path(command['args_file']).read_text(encoding='utf-8'))
                    if not isinstance(arguments, dict):
                        raise ValueError('Tool arguments phải là object JSON')
                    timeout = command.get('timeout_seconds', 60)
                    if type(timeout) is not int or not 1 <= timeout <= 660:
                        raise ValueError('Tool timeout phải1–660s; không tự tăng workload')
                    tools = await asyncio.wait_for(client.list_tools(), timeout=20)
                    if name not in {tool.name for tool in tools}:
                        raise ValueError('Tool không thuộc catalog hiện tại')
                    result = await asyncio.wait_for(client.call_tool(name, arguments), timeout=timeout)
                    value = json_value(result)
                    text = json.dumps(value, ensure_ascii=False, allow_nan=False).replace(session.wss.token, '[REDACTED]')
                    destination = directory / ('result-' + uuid.uuid4().hex + '.json')
                    destination.write_text(text+'\n', encoding='utf-8')
                    emit({'event':'tool_result', 'tool':name, 'path':str(destination.relative_to(ROOT)),
                          'preview':text[:6000], 'scope':'Inspect artifacts; exit/tool result alone is not experiment acceptance'})
                else:
                    raise ValueError('action: status/list/open/call/close')
            except Exception as error:
                emit({'event':'request_error', 'error_type':type(error).__name__, 'message':str(error)})
        emit({'event':'closing', 'connected':proxy.is_connected(), 'remote_runtime_deleted':False})
    (PRIVATE/'current.json').write_text(json.dumps({'event':'closed','connected':False})+'\n', encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--open-browser', action='store_true')
    parser.add_argument('--ttl-seconds', type=int, default=7200)
    options = parser.parse_args()
    if not 10 <= options.ttl_seconds <= 7200:
        parser.error('TTL phải10–7200s')
    asyncio.run(main(options))
