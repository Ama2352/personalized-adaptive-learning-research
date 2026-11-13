"""Profile CPU 128 window Junyi thực từ một shard, không tạo hoặc train model."""
import _thread
import cProfile
import hashlib
import io
import json
import os
from pathlib import Path
import pstats
import random
import sys
import threading
import time
import traceback
import zipfile

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).resolve().parent
os.environ.update(CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='2', MKL_NUM_THREADS='2',
                  OPENBLAS_NUM_THREADS='2', PYTHONDONTWRITEBYTECODE='1')
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT/'src'))


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    started = time.perf_counter()
    import psutil
    process = psutil.Process()
    initial_cpu = sum(process.cpu_times()[:2])
    result = dict(status='FAILED_PRESERVED', scope='CPU_GRAPH_CONTEXT_SINGLE_SHARD_DIAGNOSTIC',
        requested_windows=128, seed=43, max_rss_bytes=2*1024**3, max_wall_seconds=120,
        max_cpu_seconds=120, gpu_used=False, model_constructed=False, model_trained=False,
        full_cache_verified=False, source_run='modal-junyi-a1-b128-h100-20261113-05',
        peak_rss_bytes=process.memory_info().rss, resource_failure=None)
    stopped = threading.Event()
    def watchdog():
        while not stopped.wait(.1):
            rss = process.memory_info().rss
            cpu = sum(process.cpu_times()[:2])-initial_cpu
            result['peak_rss_bytes'] = max(result['peak_rss_bytes'], rss)
            if rss > result['max_rss_bytes'] or cpu > 120 or time.perf_counter()-started > 120:
                result['resource_failure'] = dict(rss_bytes=rss, cpu_seconds=cpu,
                    wall_seconds=time.perf_counter()-started)
                _thread.interrupt_main()
                return
    monitor = threading.Thread(target=watchdog, daemon=True)
    monitor.start()
    try:
        request = json.loads((BUNDLE/'request05.json').read_text(encoding='utf-8'))
        inputs = request['inputs']
        pins = {}
        for key, pin_key in [('roles_path','roles_sha256'), ('encoding_file','encoding_sha256'),
            ('encoding_receipt','encoding_receipt_sha256')]:
            path = ROOT/inputs[key]
            pins[inputs[key]] = sha(path)
            assert pins[inputs[key]] == inputs[pin_key]
        graph_path = ROOT/request['graph_file']
        assert sha(graph_path) == request['graph_sha256']
        pins[request['graph_file']] = request['graph_sha256']
        cache = ROOT/inputs['train_window_cache']
        manifest_path = cache/'manifest.json'
        assert sha(manifest_path) == inputs['train_window_manifest_sha256']
        pins[manifest_path.relative_to(ROOT).as_posix()] = inputs['train_window_manifest_sha256']
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        assert manifest['status'] == 'COMPLETE'
        assert json.loads((cache/'COMPLETE.json').read_text())['manifest_sha256'] == inputs['train_window_manifest_sha256']
        assert manifest['summary']['target_rows'] == 13347331
        source = ROOT/request['archives']['source']['path']
        assert sha(source) == request['archives']['source']['sha256']
        with zipfile.ZipFile(source) as saved:
            source_pins = json.loads(saved.read('MANIFEST.json'))['files']
        source_paths = ['src/knowledge_tracing/akt/'+name for name in (
            'research_graph_model.py','research_junyi_graph.py','research_junyi_data.py',
            'research_junyi_window_cache.py','research_junyi_roles.py')]
        for name in source_paths:
            pins[name] = sha(ROOT/name)
            assert pins[name] == source_pins[name]
        from knowledge_tracing.akt.research_junyi_roles import JunyiResearchRoles
        from knowledge_tracing.akt.research_junyi_data import JunyiPhaseView, load_prepared_junyi_encoding
        from knowledge_tracing.akt.research_junyi_graph import JunyiGraphCondition, JunyiGraphPhaseSession
        from knowledge_tracing.akt.research_junyi_window_cache import _load_shard, _parts
        from knowledge_tracing.akt.research_graph_model import _evidence_sha
        from knowledge_tracing.akt.types import TrainingWindow
        from knowledge_tracing.shared_kt import PrerequisiteGraph
        roles_payload = json.loads((ROOT/inputs['roles_path']).read_text(encoding='utf-8'))
        for name in ('train_users','selection_users','calibration_users','outer_validation_users'):
            roles_payload[name] = tuple(roles_payload[name])
        roles = JunyiResearchRoles(**roles_payload)
        train = JunyiPhaseView(roles,'select_train80',roles.train_users,roles.identity)
        encoding = load_prepared_junyi_encoding(ROOT/inputs['encoding_file'],ROOT/inputs['encoding_receipt'],
            view=train,source_data_sha256=manifest['key']['source_data_sha256'],
            expected_file_sha256=inputs['encoding_sha256'],expected_receipt_sha256=inputs['encoding_receipt_sha256'])
        assert train.identity == manifest['key']['phase_view_identity']
        assert encoding.identity == manifest['key']['encoding_identity'] and len(encoding.native.vocabulary.values)==717
        stored_graph = json.loads(graph_path.read_text(encoding='utf-8'))
        graph = PrerequisiteGraph.from_edges(stored_graph['nodes'],stored_graph['corrected_edges'])
        assert len(graph.edges)==976
        condition = JunyiGraphCondition(encoding,graph,request['graph_sha256'])
        phase = JunyiGraphPhaseSession(condition,train)
        shard = manifest['shards'][0]
        assert shard['name'] == 'shard-000000.npz'
        records = list(_load_shard(cache/shard['name'],shard,manifest))
        pins[(cache/shard['name']).relative_to(ROOT).as_posix()] = shard['sha256']
        assert all(type(record) is TrainingWindow for record in records) and len(records)>=128
        selected = random.Random(43).sample(records,128)
        allowed = frozenset(train.users)
        for record in selected:
            _parts(record,train,encoding,allowed)
        windows = tuple(record.window for record in selected)
        result.update(input_pins=pins, encoding_identity=encoding.identity, condition_identity=condition.identity,
            role_identity=roles.identity, phase_identity=train.identity, graph_edges=976, vocabulary=717,
            shard=shard['name'], shard_records=len(records), selected_windows=len(windows),
            targets=sum(int(window.target_mask.sum()) for window in windows),
            window_tokens=sum(len(window.inputs.item_ids) for window in windows),
            unique_learners=len({window.inputs.user_ids[0] for window in windows}),
            setup_seconds=time.perf_counter()-started)
        def operation():
            before = time.perf_counter()
            evidence = tuple(phase.prefix_evidence(window) for window in windows)
            prefix_seconds = time.perf_counter()-before
            hashes = []
            before = time.perf_counter()
            for _ in range(4):
                hashes.append(_evidence_sha(evidence))
            hashes_seconds = time.perf_counter()-before
            assert len(set(hashes))==1
            return evidence, dict(prefix_seconds=prefix_seconds, four_hashes_seconds=hashes_seconds,
                combined_seconds=prefix_seconds+hashes_seconds, evidence_sha256=hashes[0])
        evidence, result['unprofiled'] = operation()
        queries = [item for row in evidence for item in row if item is not None]
        lengths = sorted(len(item.audit.observed_rows) for item in queries)
        result['evidence_statistics'] = dict(queries=len(queries), parent_records=sum(len(item.audit.parents) for item in queries),
            active_queries=sum(any(parent.support>0 for parent in item.audit.parents) for item in queries),
            observed_rows_sum=sum(lengths), observed_rows_max=max(lengths,default=0),
            observed_rows_median=lengths[len(lengths)//2] if lengths else 0)
        profile = cProfile.Profile()
        evidence_profiled, result['profiled'] = profile.runcall(operation)
        assert result['profiled']['evidence_sha256'] == result['unprofiled']['evidence_sha256']
        profile.dump_stats(str(BUNDLE/'actual-graph-cpu.pstats'))
        text = io.StringIO()
        stats = pstats.Stats(profile,stream=text).strip_dirs().sort_stats('cumulative')
        stats.print_stats(35)
        (BUNDLE/'actual-graph-cpu-top.txt').write_text(text.getvalue(),encoding='utf-8')
        rows = []
        for (filename,line,function),(primitive,calls,self_seconds,cumulative,callers) in stats.stats.items():
            rows.append(dict(file=filename,line=line,function=function,primitive_calls=primitive,calls=calls,
                self_seconds=self_seconds,cumulative_seconds=cumulative))
        result['top_cumulative'] = sorted(rows,key=lambda row:row['cumulative_seconds'],reverse=True)[:35]
        result['hot_functions'] = [row for row in rows if row['function'] in (
            'prefix_evidence','_light_check','_prefix_evidence','_evidence_sha','_validate_window','_asdict_inner','asdict','dumps')]
        phase.assert_boundary()
        assert all(sha(ROOT/name)==digest for name,digest in pins.items())
        result['status'] = 'PASS_ACTUAL_TRAIN80_SHARD_CPU_PROFILE'
    except BaseException as error:
        result.update(error_type=type(error).__name__,error=str(error),traceback=traceback.format_exc())
    finally:
        stopped.set()
        monitor.join(timeout=1)
        result.update(wall_seconds=time.perf_counter()-started,
            process_cpu_seconds=sum(process.cpu_times()[:2])-initial_cpu,
            limits_vi='128 cửa sổ lấy mẫu seed43 trong shard đầu tiên, không là thứ tự shuffle toàn epoch. '
                'Chỉ kiểm pin manifest, shard đã đọc và geometry mẫu, chưa kiểm toàn cache/whole-dataset reproducibility. '
                'Không model, tensor CUDA, forward/backward hoặc optimizer. Profile chỉ CPU prefix/evidence/hash, '
                'không gồm GPU transfers, batch hashes, checkpoint hoặc các integrity checks của adapter ngoài phạm vi. '
                'cProfile có overhead, đối chiếu thêm số đo unprofiled. Metadata roles được đọc để dựng đúng TRAIN80, '
                'không đọc events calibration/Holdout.')
        with (BUNDLE/'actual-graph-cpu-profile.json').open('x',encoding='utf-8') as stream:
            json.dump(result,stream,ensure_ascii=False,indent=2)
            stream.write('\n')
        print(json.dumps({key:value for key,value in result.items() if key not in ('top_cumulative','input_pins','traceback')},ensure_ascii=False))
    return 0 if result['status']=='PASS_ACTUAL_TRAIN80_SHARD_CPU_PROFILE' else 1


if __name__=='__main__':
    raise SystemExit(main())
