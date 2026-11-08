"""Lệnh AKT có phase tường minh và mặc định không chạy training."""

from .watchdog import main


if __name__ == '__main__':
    raise SystemExit(main())
