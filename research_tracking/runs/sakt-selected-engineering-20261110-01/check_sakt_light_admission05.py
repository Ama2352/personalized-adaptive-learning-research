"""Kiểm RAM trước lượt retry đã duyệt, không model hoặc NN imports."""
from pathlib import Path
import ctypes
import json
import time

PREP = Path(__file__).resolve().parent


class Memory(ctypes.Structure):
    _fields_ = [('length', ctypes.c_ulong), ('load', ctypes.c_ulong)] + [
        (name, ctypes.c_ulonglong) for name in ('total', 'available', 'page', 'available_page',
                                             'virtual', 'available_virtual', 'extended')]


samples = []
for _ in range(3):
    value = Memory()
    value.length = ctypes.sizeof(value)
    assert ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(value))
    samples.append(value.available)
    time.sleep(.2)
minimum = 4 * 1024**3 + 128 * 1024**2
accepted = min(samples) >= minimum
result = dict(accepted=accepted, available_ram_samples=samples,
    canonical_inside_worker_floor_bytes=4*1024**3, additional_light_launcher_headroom_bytes=128*1024**2,
    note='Extra root admission choice for lightweight cmd launcher; actual canonical preallocation4GiB remains mandatory.')
with (PREP / 'sakt-retry05-light-admission02.json').open('x') as stream:
    json.dump(result, stream, indent=2)
print(json.dumps(result))
raise SystemExit(0 if accepted else 1)
