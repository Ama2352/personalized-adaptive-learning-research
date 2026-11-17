"""Hàng đợi hữu hạn A1–A3 sau A0, một CPU export mỗi lúc, không GPU."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent
CACHE=ROOT/'artifacts/akt/local-calibration/20261117'
PYTHON=ROOT/'.venv/Scripts/python.exe'

def wait_for(path):
    start=time.monotonic()
    while not path.is_file():
        if time.monotonic()-start>3600:
            raise TimeoutError('Mốc đầu vào chưa hoàn tất trong một giờ')
        time.sleep(15)

def main():
    import psutil
    wait_for(CACHE/'outer-export01/A0/METRICS.json')
    environment=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='2')
    for variant in ('A1','A2','A3'):
        wait_for(B/(variant+'_DRIVE_BACKUP01.json'))
        subprocess.run([str(PYTHON),str(B/'prepare_cpu_request01.py'),'--variant',variant],cwd=ROOT,check=True)
        request=B/(variant+'_CPU_EXPORT_REQUEST01.json')
        digest=hashlib.sha256(request.read_bytes()).hexdigest()
        started=time.monotonic();peak=0
        with (B/(variant.lower()+'-cpu-export01.txt')).open('x',encoding='utf-8') as log:
            process=subprocess.Popen([str(PYTHON),'-u',str(ROOT/'scripts/akt/outer_numeric_cpu_export.py'),
                '--request',str(request),'--request-sha256',digest],cwd=ROOT,env=environment,
                stdout=log,stderr=subprocess.STDOUT)
            monitored=psutil.Process(process.pid)
            try:
                while process.poll() is None:
                    children=monitored.children(recursive=True)
                    rss=sum(p.memory_info().rss for p in [monitored,*children] if p.is_running())
                    peak=max(peak,rss)
                    if rss>2*1024**3 or time.monotonic()-started>7200:
                        raise RuntimeError('CPU export vượt giới hạn2GiB hoặc hai giờ')
                    time.sleep(5)
                if process.returncode:
                    raise RuntimeError('CPU export dừng, xem log đã giữ')
            finally:
                if process.poll() is None:
                    for child in monitored.children(recursive=True):
                        child.terminate()
                    process.terminate();process.wait(timeout=15)
        result=dict(status='CPU_EXPORT_METRICS_COMPLETE',variant=variant,
            seconds=time.monotonic()-started,sampled_peak_process_tree_rss_bytes=peak)
        (B/(variant+'_CPU_RESOURCE01.json')).write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result),flush=True)

if __name__=='__main__':
    main()
