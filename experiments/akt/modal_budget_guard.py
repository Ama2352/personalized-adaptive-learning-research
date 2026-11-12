"""Watchdog local cho đúng App Modal của một lượt đã được cấp ngân sách.

Deadline phải tạo trước app.run để tính cả startup. Callback dừng App có timeout
riêng. Helper không cấp quyền chạy hoặc suy ngân sách từ billing có độ trễ.
"""
from dataclasses import asdict, dataclass, field
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
import uuid


class ModalDeadlineExceeded(TimeoutError):
    pass


class ModalStopUnconfirmed(RuntimeError):
    pass


class ModalGuardDiagnosticError(RuntimeError):
    pass


def _validate_run_name(run_id, app_name):
    if (type(run_id) is not str
            or re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,79}', run_id) is None
            or app_name != 'kltn-akt-'+run_id):
        raise ValueError('Explicit owned App name/run binding required')


@dataclass(frozen=True)
class OwnedModalApp:
    run_id: str
    app_id: str
    app_name: str

    def __post_init__(self):
        _validate_run_name(self.run_id, self.app_name)
        if (type(self.app_id) is not str or re.fullmatch(r'ap-[A-Za-z0-9]+', self.app_id) is None):
            raise ValueError('Explicit owned App ID/name/run binding required')


@dataclass(frozen=True)
class PendingOwnedModalApp:
    """Provider chỉ đọc app.app_id từ chính App vừa tạo cho run này."""
    run_id: str
    app_name: str
    app_id_provider: object = field(repr=False)

    def __post_init__(self):
        _validate_run_name(self.run_id, self.app_name)
        if not callable(self.app_id_provider):
            raise ValueError('Owned App object ID provider required')

    def resolve(self):
        app_id = self.app_id_provider()
        if app_id is None:
            raise RuntimeError('Owned App ID unavailable; stop cannot be confirmed')
        return OwnedModalApp(self.run_id, app_id, self.app_name)


class ModalRunDeadline:
    def __init__(self, max_seconds, *, started_at=None, clock=time.monotonic):
        if (type(max_seconds) not in (int, float)
                or not math.isfinite(max_seconds) or max_seconds <= 0):
            raise ValueError('Finite positive total run deadline required')
        self.clock = clock
        self.started_at = clock() if started_at is None else started_at
        if (type(self.started_at) not in (int, float)
                or not math.isfinite(self.started_at) or self.started_at > clock()):
            raise ValueError('Valid monotonic start time required')
        self.max_seconds = float(max_seconds)

    def seconds_left(self):
        return max(0., self.started_at+self.max_seconds-self.clock())

    def remaining(self):
        value = self.seconds_left()
        if value <= 0:
            raise ModalDeadlineExceeded('Total Modal startup/execution deadline reached')
        return value


def stop_owned_app_cli(app, *, timeout_seconds=15):
    """Dừng đúng ID; xác nhận lại trạng thái nếu CLI báo App đã dừng."""
    if type(app) is not OwnedModalApp:
        raise ValueError('Typed owned App binding required')
    if (type(timeout_seconds) not in (int, float)
            or not math.isfinite(timeout_seconds) or not 0 < timeout_seconds <= 30):
        raise ValueError('Bounded stop command timeout required')
    deadline = time.monotonic()+timeout_seconds
    def remaining():
        value = deadline-time.monotonic()
        if value <= 0:
            raise subprocess.TimeoutExpired('modal app stop/state confirmation',timeout_seconds)
        return value
    try:
        subprocess.run([sys.executable, '-B', '-m', 'modal', 'app', 'stop', '--yes', app.app_id],
            check=True, timeout=remaining(), capture_output=True, text=True)
    except subprocess.CalledProcessError as stop_error:
        # CLI có thể trả code1 khi App đã kết thúc. Không suy trạng thái từ stderr.
        for attempt in range(3):
            result = subprocess.run([sys.executable,'-B','-m','modal','app','list','--json'],
                check=True,timeout=remaining(),capture_output=True,text=True)
            records = json.loads(result.stdout)
            matches = [row for row in records if type(row) is dict and row.get('app_id')==app.app_id] if type(records) is list else []
            if (len(matches)==1 and matches[0].get('state')=='stopped'
                    and type(matches[0].get('tasks')) in (int,str)
                    and matches[0]['tasks'] in (0,'0')):
                return
            if attempt < 2:
                time.sleep(min(.5, remaining()))
        raise RuntimeError('Owned App was not independently confirmed stopped with zero tasks') from stop_error


class ModalAppBudgetGuard:
    """Dừng ở deadline từ thread độc lập và luôn dừng App khi thoát context.

stop_app nhận OwnedModalApp và phải dừng đúng App đó. Callback thành công là
acknowledgement; caller kiểm trạng thái server sau đó trước lượt trả phí mới.
Nếu máy local tắt/mất mạng, watchdog local không bảo đảm remote đã dừng.
"""
    def __init__(self, app, deadline, *, stop_app, diagnostic_path, stop_wait_seconds=20):
        if type(app) not in (OwnedModalApp, PendingOwnedModalApp) or type(deadline) is not ModalRunDeadline or not callable(stop_app):
            raise ValueError('Owned App, total deadline and explicit stop callback required')
        if (type(stop_wait_seconds) not in (int, float)
                or not math.isfinite(stop_wait_seconds) or not 0 < stop_wait_seconds <= 60):
            raise ValueError('Bounded stop acknowledgement wait required')
        self.app, self.deadline, self.stop_app = app, deadline, stop_app
        self.diagnostic_path = Path(diagnostic_path)
        self.stop_wait_seconds = stop_wait_seconds
        self._lock = threading.RLock()
        self._cancel_watchdog = threading.Event()
        self._stop_done = threading.Event()
        self._stop_started = False
        self._timed_out = False
        self._entered = False
        self._diagnostic_error = None
        self._status = dict(app=dict(run_id=app.run_id, app_id=getattr(app,'app_id',None), app_name=app.app_name),
            max_seconds=deadline.max_seconds,
            started_at_monotonic=deadline.started_at, events=[], stop_acknowledged=False)

    def _record(self, event, **fields):
        with self._lock:
            self._status['events'].append(dict(event=event,
                elapsed_seconds=self.deadline.clock()-self.deadline.started_at, **fields))
            try:
                self.diagnostic_path.parent.mkdir(parents=True, exist_ok=True)
                temp = self.diagnostic_path.with_name(self.diagnostic_path.name+'.tmp')
                with temp.open('w', encoding='utf-8') as stream:
                    json.dump(self._status, stream, ensure_ascii=False, indent=2, allow_nan=False)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temp, self.diagnostic_path)
            except OSError as error:
                # Hỏng nơi lưu log vẫn phải gửi lệnh dừng tài nguyên.
                self._diagnostic_error = error

    def _stop_worker(self):
        try:
            resolved = self.app.resolve() if type(self.app) is PendingOwnedModalApp else self.app
            with self._lock:
                self._status['app'] = asdict(resolved)
            self._record('owned_app_bound')
            self.stop_app(resolved)
        except BaseException as error:
            self._record('stop_failed', error_type=type(error).__name__, error=str(error))
        else:
            with self._lock:
                self._status['stop_acknowledged'] = True
            self._record('stop_acknowledged')
        finally:
            self._stop_done.set()

    def _request_stop(self, reason):
        with self._lock:
            if self._stop_started:
                return
            self._stop_started = True
            self._record('stop_requested', reason=reason)
            threading.Thread(target=self._stop_worker, name='modal-app-stop', daemon=True).start()

    def _watchdog(self):
        if not self._cancel_watchdog.wait(self.deadline.seconds_left()):
            self._timed_out = True
            self._request_stop('total_deadline')

    def __enter__(self):
        if self._entered:
            raise ValueError('Fresh single-use Modal guard diagnostic required')
        if self.diagnostic_path.exists():
            original = self.diagnostic_path
            self.diagnostic_path = original.with_name(original.name+'.arm-error-'+uuid.uuid4().hex+'.json')
            self._entered = True
            error = ValueError('Fresh Modal guard diagnostic required; existing diagnostic preserved')
            self._record('arm_failed', original_diagnostic=str(original))
            self.__exit__(ValueError, error, None)
            raise error
        self._entered = True
        self._record('armed')
        threading.Thread(target=self._watchdog, name='modal-app-deadline', daemon=True).start()
        if self._diagnostic_error is not None:
            self.__exit__(ModalGuardDiagnosticError, self._diagnostic_error, None)
        return self

    def remaining(self):
        if self._stop_started:
            raise ModalDeadlineExceeded('Modal App stop has already been requested')
        return self.deadline.remaining()

    def __exit__(self, error_type, error, traceback):
        self._cancel_watchdog.set()
        self._timed_out = self._timed_out or self.deadline.seconds_left() <= 0
        self._request_stop('total_deadline' if self._timed_out else 'exception' if error else 'completed')
        acknowledged_in_time = self._stop_done.wait(self.stop_wait_seconds)
        if not acknowledged_in_time or not self._status['stop_acknowledged']:
            self._record('stop_unconfirmed', wait_seconds=self.stop_wait_seconds)
            raise ModalStopUnconfirmed('App stop unconfirmed; inspect diagnostics before any new paid run') from error
        if self._timed_out:
            raise ModalDeadlineExceeded('Total Modal startup/execution deadline reached; App stop acknowledged') from error
        if self._diagnostic_error is not None:
            raise ModalGuardDiagnosticError('App stop acknowledged but guard diagnostics could not be persisted') from self._diagnostic_error
        return False
