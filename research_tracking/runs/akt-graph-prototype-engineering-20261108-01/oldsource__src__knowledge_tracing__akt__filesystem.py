"""Công bố file hoàn chỉnh mà không ghi đè artifact đã tồn tại."""

import os
from pathlib import Path


def publish_new_file(source: Path, destination: Path) -> None:
    """Nhận file tạm đã đóng trên cùng filesystem, rồi chuyển sang tên cuối.

    Windows rename từ chối destination tồn tại. POSIX dùng hard link vì
    rename trên POSIX có thể ghi đè. Lỗi quyền hoặc filesystem được giữ nguyên.
    """
    if os.name == 'nt':
        os.rename(source, destination)
    else:
        os.link(source, destination)
        source.unlink()
