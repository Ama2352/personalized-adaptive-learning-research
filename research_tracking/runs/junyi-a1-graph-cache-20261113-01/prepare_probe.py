"""Tạo probe từ phép đo T4 đã lưu, đối chiếu compact trực tiếp và cache SQLite."""
from pathlib import Path
import ast
import hashlib
import json
import zipfile

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
source=ROOT/'research_tracking/runs/junyi-a1-real-t4-20261113-01/probe_real_t4.py'
code='\n'.join(line for line in source.read_text(encoding='utf-8').splitlines() if line.strip())+'\n'
code=code.replace("max_steps=32,max_seconds=175", "max_steps=192,max_seconds=175")
code=code.replace('max_total_targets=262144','max_total_targets=2097152')
code=code.replace("+1<=32", "+1<=192").replace("+count<=262144", "+count<=2097152")
code=code.replace("compact_context=name=='compact'", "compact_context=True,context_cache=cache_reader if name=='compact' else None")
insert='''        from knowledge_tracing.akt.research_junyi_graph_cache import build_graph_context_cache,GraphContextCache
        from knowledge_tracing.akt.research_junyi_compact import build_compact_context
        # Build CPU trước khi khởi tạo model CUDA, giữ riêng chi phí cold.
        binding=dict(dataset_sha256=hashlib.sha256((data/'cohort.json').read_bytes()).hexdigest(),
                     window_manifest_sha256=hashlib.sha256((data/'train.npz').read_bytes()).hexdigest())
        cache_path=root/'artifacts/akt/graph-context-cache/probe-train.sqlite'
        receipt=build_graph_context_cache(cache_path,iter(entries),session,**binding,
            expected_windows=len(entries),expected_targets=cohort['outputs']['train']['targets'],
            max_seconds=30,max_rss_bytes=2*1024**3)
        cache_reader=GraphContextCache.open(cache_path,receipt['cache_sha256'],session,**binding)
        for group in (tuple(e.window for e in entries[:128]),tuple(e.window for e in reversed(entries[128:])),
                      tuple(e.window for e in entries[17:114])):
            assert cache_reader.batch(group,session)==build_compact_context(group,session)
        result['graph_cache']=receipt
        result['methods']=dict(reference='A1 compact trực tiếp',compact='A1 compact cache SQLite')
'''
code=code.replace('        adapters={}\n',insert+'        adapters={}\n')
# Hai lượt warmup không đưa vào thời gian đo, sau đó ABBA 10 giây/block.
code=code.replace('            torch.cuda.synchronize()\n            at=time.perf_counter()',
    "            for warm in range(2): train_step(adapter,entries[warm*128:(warm+1)*128],optimizer)\n            torch.cuda.synchronize()\n            at=time.perf_counter()")
code=code.replace('            for _ in range(2):\n                io_at=',
    '            measured_steps=0\n            while time.perf_counter()-at<10:\n                io_at=')
code=code.replace('                    train_step(adapter,group,optimizer)\n                    input_targets',
    '                    train_step(adapter,group,optimizer)\n                    measured_steps+=1\n                    input_targets')
code=code.replace('method=name,block=block,steps=4','method=name,block=block,steps=measured_steps')
# Mỗi ABBA block bắt đầu lại cùng trọng số/optimizer, cuối cùng so trên cùng state.
code=code.replace("        result['validation']=[]", "        terminal_optimizer=adapters['compact']._optimizer.state_dict()\n        terminal_model={key:value.detach().cpu().clone() for key,value in adapters['compact'].native.state_dict().items()}\n        terminal_cpu_rng=torch.get_rng_state().clone()\n        terminal_cuda_rng=torch.cuda.get_rng_state(0).clone()\n        for adapter in adapters.values(): reset(adapter,.75)\n        result['validation']=[]")
code=code.replace('optimizer=adapter._optimizer.state_dict()', 'optimizer=terminal_optimizer')
code=code.replace('model=adapter.native.state_dict()', 'model=terminal_model')
code=code.replace('cpu=torch.get_rng_state(),cuda=torch.cuda.get_rng_state(0)', 'cpu=terminal_cpu_rng,cuda=terminal_cuda_rng')
code=code.replace("        torch.save(terminal,output/'BENCHMARK_STATE.pt')", "        torch.save(terminal,output/'BENCHMARK_STATE.pt')\n        reloaded=torch.load(output/'BENCHMARK_STATE.pt',map_location='cpu',weights_only=False)\n        result['checkpoint_reload_max_drift']=compare(reloaded['model'],terminal_model)")
code=code.replace("'PASS_REAL_JUNYI_T4_BOUNDED_THROUGHPUT'", "'PASS_REAL_JUNYI_T4_GRAPH_CACHE'")
code=code.replace("scope='REAL_JUNYI_T4_BOUNDED_THROUGHPUT'", "scope='REAL_JUNYI_T4_GRAPH_CACHE'")
ast.parse(code)
(HERE/'probe_t4.py').write_text(code,encoding='utf-8')
# Kiểm config bằng cùng bộ validator, chưa cấp CUDA/model.
import sys
sys.path.insert(0,str(ROOT/'src'))
from knowledge_tracing.akt.config import AKTConfig,ResearchCUDAExecutionProfile,validate_config
from dataclasses import replace
tree=ast.parse(code)
assignment=next(node for node in ast.walk(tree) if isinstance(node,ast.Assign)
                and any(isinstance(t,ast.Name) and t.id=='config' for t in node.targets))
profile=ResearchCUDAExecutionProfile(12*1024**3,recipe_id='cgakt-cuda-fp32-batch128-v2')
config=eval(compile(ast.Expression(assignment.value),'probe-config','eval'),
            dict(replace=replace,AKTConfig=AKTConfig,root=ROOT))
validate_config(config,cuda_profile=profile)
(HERE/'config-check.json').write_text(json.dumps(dict(status='PASS_STATIC_CONFIG',
    batch_size=config.batch_size,run_id=config.run_id,max_steps=config.max_steps,
    probe_sha256=hashlib.sha256(code.encode()).hexdigest()),indent=2)+'\n')
archive=ROOT/'artifacts/akt/colab/junyi-a1-graph-cache-20261113-01.zip'
files={}
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as saved:
    # Giữ nguyên inventory của gói đã được phép, cập nhật source hiện hành.
    previous=ROOT/'artifacts/akt/colab/junyi-a1-real-t4-20261113-01.zip'
    with zipfile.ZipFile(previous) as old:
        inventory=json.loads(old.read('INVENTORY.json'))
        for name in inventory:
            if name.startswith('src/') and (ROOT/name).exists(): payload=(ROOT/name).read_bytes()
            elif name.endswith('.py') and not name.startswith('src/'): continue
            else: payload=old.read(name)
            saved.writestr(name,payload);files[name]=hashlib.sha256(payload).hexdigest()
    for name,path in [('probe_t4.py',HERE/'probe_t4.py'),
                      ('src/knowledge_tracing/akt/research_junyi_graph_cache.py',ROOT/'src/knowledge_tracing/akt/research_junyi_graph_cache.py')]:
        if name not in files:
            payload=path.read_bytes();saved.writestr(name,payload);files[name]=hashlib.sha256(payload).hexdigest()
    saved.writestr('INVENTORY.json',json.dumps(files,sort_keys=True))
(HERE/'transfer-manifest.json').write_text(json.dumps(dict(path=archive.relative_to(ROOT).as_posix(),
    sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),bytes=archive.stat().st_size,files=files),indent=2)+'\n')
print(json.dumps(dict(status='PREPARED',bytes=archive.stat().st_size,files=len(files))))
