"""Đóng gói source tối thiểu và phép kiểm T4, không có dữ liệu người học."""
import ast
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OLD = ROOT/'research_tracking/runs/junyi-a1-selected-20261113-01'
REQUESTS = ROOT/'artifacts/akt/colab/requests'
SOURCE = ROOT/'src/knowledge_tracing/akt/research_graph_model.py'
old_sha = hashlib.sha256((OLD/'research_graph_model_source2.py').read_bytes()).hexdigest()
new_sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest()

# Đo helper thuần stdlib ở local, không import Torch khi RAM máy hạn chế.
tree = ast.parse(SOURCE.read_text(encoding='utf-8'))
selected = [node for node in tree.body if isinstance(node, ast.FunctionDef)
            and node.name in ('_need', '_evidence_sha', '_evidence_json_default')]
assert len(selected) == 3
import dataclasses
namespace = dict(hashlib=hashlib, json=json, fields=dataclasses.fields,
                 is_dataclass=dataclasses.is_dataclass)
exec(compile(ast.Module(body=selected, type_ignores=[]), str(SOURCE), 'exec'), namespace)
spec = importlib.util.spec_from_file_location('fixture', OLD/'benchmark_evidence_projector.py')
fixture = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = fixture
spec.loader.exec_module(fixture)
import time
measurements = []
for dense in (False, True):
    rows = fixture.fixture(dense)
    samples = []
    for method in ('legacy', 'candidate', 'candidate', 'legacy'):
        at = time.perf_counter()
        digest = (fixture.evidence_hash(rows, dataclasses.asdict) if method == 'legacy'
                  else namespace['_evidence_sha'](rows))
        samples.append(dict(method=method, seconds=time.perf_counter()-at, sha256=digest))
    assert len({item['sha256'] for item in samples}) == 1
    means = {name:sum(x['seconds'] for x in samples if x['method']==name)/2
             for name in ('legacy','candidate')}
    measurements.append(dict(dense=dense, samples=samples, speedup=means['legacy']/means['candidate']))
(HERE/'local-helper-benchmark.json').write_text(json.dumps(dict(
    status='PASS_ISOLATED_HELPER_HASH_PARITY', old_source_sha256=old_sha,
    candidate_source_sha256=new_sha, fixtures=measurements,
    scope_vi='AST helper thuần stdlib, chưa là kiểm import/model/CUDA hoặc toàn Junyi.'), indent=2)+'\n', encoding='utf-8')

probe = (OLD/'probe_gpu_vector_parity.py').read_text(encoding='utf-8')
probe = probe.replace("OLD_SHA = '997fe9191388738954c0f4aeb1f7062c9c1e3cf6646a5b2486d2618b5c02c177'", f'OLD_SHA = {old_sha!r}')
probe = probe.replace("NEW_SHA = '3a3a45634ba7ea84572f57c1828b28a705b9d2a8a10f8476510cf682507e5'", f'NEW_SHA = {new_sha!r}')
# Thay SHA chính xác, tránh nhận nhầm bản nguồn.
start = probe.index('NEW_SHA = ')
end = probe.index('\n', start)
probe = probe[:start]+f'NEW_SHA = {new_sha!r}'+probe[end:]
probe = probe.replace('H100', 'T4').replace('SCALAR_VECTOR', 'EVIDENCE_JSON')
probe = probe.replace('16*1024**3', '12*1024**3')
probe = probe.replace('signal.alarm(90)', 'signal.alarm(180)')
probe = probe.replace('max_wall_seconds=90', 'max_wall_seconds=180')
probe = probe.replace('max_seconds=85', 'max_seconds=175')
probe = probe.replace("        assert sha(old_path) == OLD_SHA", '''        # Chuỗi ngắn gồm bind, forward, backward, clip và Adam. Không sinh lại
        # prefix trong vòng đo, vì vậy chưa đại diện toàn producer Junyi.
        import subprocess
        telemetry_stop = threading.Event()
        samples = []
        phase_name = ['idle']
        def sample_gpu():
            while not telemetry_stop.wait(.25):
                row = subprocess.run(['nvidia-smi','--query-gpu=utilization.gpu,memory.used,power.draw',
                    '--format=csv,noheader,nounits'], capture_output=True, text=True, timeout=3)
                samples.append(dict(phase=phase_name[0], monotonic=time.monotonic(),
                                    values=row.stdout.strip(), returncode=row.returncode))
        telemetry = threading.Thread(target=sample_gpu, daemon=True)
        telemetry.start()
        result['short_training'] = []
        try:
            for name,native in [('old',old),('new',new)]:
                native.load_state_dict(initial, strict=True)
                with torch.no_grad():
                    native.alpha.fill_(.75)
                optimizer = torch.optim.Adam(native.parameters(), lr=config.lr, foreach=False, fused=False)
                torch.manual_seed(84)
                torch.cuda.manual_seed_all(84)
                phase_name[0] = name
                torch.cuda.synchronize()
                at = time.perf_counter()
                for step in range(6):
                    optimizer.zero_grad(set_to_none=True)
                    native.bind(batch,evidence,enabled=True)
                    loss,_,count = native(batch.q_data,batch.qa_data,batch.loss_targets)
                    (loss/count).backward()
                    torch.nn.utils.clip_grad_norm_(native.parameters(),config.max_grad_norm,error_if_nonfinite=True)
                    optimizer.step()
                torch.cuda.synchronize()
                elapsed = time.perf_counter()-at
                result['short_training'].append(dict(method=name,steps=6,seconds=elapsed,
                    targets_per_second=6*12800/elapsed))
                phase_name[0] = 'idle'
        finally:
            telemetry_stop.set()
            telemetry.join(timeout=4)
            result['gpu_samples'] = samples
        result['limits_vi'] = ('Dữ liệu tổng hợp, sáu bước mỗi bản, prefix dựng trước. '
            'Chưa chứng minh GPU trung bình 50% hoặc thời gian toàn epoch Junyi/H100.')
        assert sha(old_path) == OLD_SHA''')
(HERE/'probe_t4.py').write_text(probe, encoding='utf-8')
compile(probe, 'probe_t4.py', 'exec')

contents = {p.relative_to(ROOT).as_posix():p.read_bytes()
            for p in (ROOT/'src/knowledge_tracing').rglob('*.py')}
contents['src/knowledge_tracing/akt/research_graph_model.py'] = (OLD/'research_graph_model_source2.py').read_bytes()
for p in (ROOT/'docs/thesis_recovery').glob('*.md'):
    if p.name.startswith(('21_', '22_', '23_', '26_', '28_')):
        contents[p.relative_to(ROOT).as_posix()] = p.read_bytes()
contents['candidate/src/knowledge_tracing/akt/research_graph_model.py'] = SOURCE.read_bytes()
contents['probe_t4.py'] = probe.encode()
contents['tests/akt/test_evidence_json_hash.py'] = (ROOT/'tests/akt/test_evidence_json_hash.py').read_bytes()
inventory = {name:hashlib.sha256(data).hexdigest() for name,data in contents.items()}
archive_path = ROOT/'artifacts/akt/colab/a1-fastpath-t4-20261113-01.zip'
with zipfile.ZipFile(archive_path, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
    for name,data in contents.items():
        archive.writestr(name,data)
    archive.writestr('INVENTORY.json',json.dumps(inventory))
payload = archive_path.read_bytes()
digest = hashlib.sha256(payload).hexdigest()
(HERE/'source-transfer-manifest.json').write_text(json.dumps(dict(
    archive=str(archive_path.relative_to(ROOT)), bytes=len(payload), sha256=digest,
    files=inventory, scope='source_and_synthetic_probe_only'),indent=2)+'\n',encoding='utf-8')
encoded = base64.b64encode(payload).decode()
chunks = [encoded[index:index+45000] for index in range(0,len(encoded),45000)]
for index,chunk in enumerate(chunks):
    code = 'import base64\nfrom pathlib import Path\n'
    code += "p=Path('/content/kltn-a1-fastpath-transfer'); p.mkdir(exist_ok=True)\n"
    code += f"(p/'chunk-{index:03d}').write_text({chunk!r})\nprint('CHUNK {index}/{len(chunks)} STORED')\n"
    request = dict(cellId='0AXUvSIhLW1k',content=code)
    (REQUESTS/f'a1-fast-chunk-{index:03d}.json').write_text(json.dumps(request),encoding='utf-8')
print(json.dumps(dict(source_bytes=len(payload),sha256=digest,chunks=len(chunks),cpu=measurements)))
