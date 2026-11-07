"""Run from the checkout: .venv Python -m src.research_demo [--port 8765]."""
import argparse

from .evidence import EvidenceError
from .server import make_server


def main():
    parser = argparse.ArgumentParser(description="Demo artifact synthetic chỉ đọc, localhost")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    try:
        server = make_server(args.port)
    except (EvidenceError, OSError, ValueError) as exc:
        parser.exit(2, "Không khởi động demo: " + str(exc) + "\n")
    print(f"Đã kiểm SHA 3 manifest + 3 selected outputs. http://127.0.0.1:{server.server_port} • Ctrl+C để đóng", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
