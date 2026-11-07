"""Owned loopback visual-QA session, auto-close after 180s or stop marker."""
from pathlib import Path
import json
import sys
import threading
import time

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from src.research_demo.server import make_server

OUT=Path(__file__).resolve().parent
server=make_server(0)
start=time.monotonic()
stop=OUT/"preview-stop"
def bounded_shutdown():
    while time.monotonic()-start < 180 and not stop.exists():
        time.sleep(.2)
    server.shutdown()
threading.Thread(target=bounded_shutdown,daemon=True).start()
print(f"http://127.0.0.1:{server.server_port}",flush=True)
with (OUT/"preview-listener.json").open("x",encoding="utf8") as stream:
    json.dump({"address":server.server_address,"max_seconds":180,"purpose":"purpose-built browser QA; synthetic stored artifacts only"},stream,indent=2)
try:
    server.serve_forever()
finally:
    server.server_close()
    with (OUT/"preview-shutdown.json").open("x",encoding="utf8") as stream:
        json.dump({"listener_closed":True,"elapsed_seconds":time.monotonic()-start},stream,indent=2)
    print("Owned demo listener closed",flush=True)
