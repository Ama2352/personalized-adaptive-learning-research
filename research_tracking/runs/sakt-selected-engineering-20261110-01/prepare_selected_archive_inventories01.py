"""Chuẩn bị inventory bằng chứng đã có, không test/model hoặc giải thuật khoa học."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def copy_record(path):
    assert path.is_file() and path.stat().st_size <= 2**20, path
    return dict(path=path.relative_to(ROOT).as_posix(), sha256=sha(path), bytes=path.stat().st_size)


def add(copies, alias, path):
    assert alias not in copies, alias
    copies[alias] = copy_record(path)


def flat(copies, name, alias):
    # Chỉ flat files của namespace đã chỉ định, không TEMP hoặc cache/runtime.
    for path in sorted((PREP/name).iterdir()):
        if path.is_file(): add(copies, alias+'__'+path.name, path)


def refs(names):
    return {name:sha(ROOT/name) for name in names}


def save(name, value):
    path = PREP/name
    with path.open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode())
    print(json.dumps(dict(file=name, sha256=sha(path), copies=len(value['copies']), copy_bytes=sum(v['bytes'] for v in value['copies'].values()))))


def main60():
    final = read(PREP/'main60-graph-conditions02-owned/final.json')
    result = read(PREP/'main60-graph-conditions02/result.json')
    assert final['status'] == 'ACCEPTED_SIX_MAIN60_CONDITION_BINDINGS_NO_MODELS' and final['errors'] == []
    assert result['source_before'] == result['source_after'] and result['input_before'] == result['input_after']
    summary = result['summary']; assert len(summary['conditions']) == 6 and summary['loader_calls'] == 2
    assert summary['new_surrogate_fits'] == summary['neural_model_calls'] == summary['optimizer_calls'] == summary['teacher_calls'] == 0
    copies = {}
    for n in ['MAIN60_GRAPH_CONFIDENCE_REUSE_PLAN01.md', 'MAIN60_GRAPH_CONFIDENCE_REUSE_PLAN01.json',
              'MAIN60_GRAPH_BINDING_READINESS_REPORT01.md', 'prepare_selected_archive_inventories01.py',
              'check_main60_graph_bindings01.py', 'run_main60_graph_bindings01.py', 'main60_graph_bindings01_packet.json',
              'check_main60_graph_bindings02.py', 'run_main60_graph_bindings02.py', 'main60_graph_bindings02_packet.json']:
        add(copies, n, PREP/n)
    for attempt in ('01', '02'):
        flat(copies, 'main60-graph-conditions'+attempt, 'binder'+attempt)
        flat(copies, 'main60-graph-conditions'+attempt+'-owned', 'owned'+attempt)
    run = read(PREP/'method24_run01.json')
    native_refs = [dict(path=(PREP/'method24-native01'/name).relative_to(ROOT).as_posix(), bytes=row['bytes'],
        sha256=row['sha256'], verify_sha_at_archive=False, copied=False,
        sha_scope='ACTUAL_ACCEPTED_METHOD24_PRODUCER_AND_BINDER02_TWO_LOADER_VERIFICATIONS') for name,row in run['artifacts'].items()]
    assert len(native_refs) == 14 and sum(v['bytes'] for v in native_refs) == 69519761
    reference = refs(['research_tracking/runs/edge-confidence-windows-bootstrap-20261108-01/manifest.json',
        'research_tracking/runs/edge-confidence-artifact-integration-20261109-01/manifest.json',
        'src/knowledge_tracing/evidence.py'])
    return dict(run_id='main60-graph-condition-binding-20261110-01', copies=copies, references_sha256=reference,
        native_references=native_refs, original_source_inventory=result['source_before'],
        accepted_outer=(PREP/'main60-graph-conditions02-owned/final.json').relative_to(ROOT).as_posix(),
        accepted_status=final['status'], reference_limit_vi='14file lớn chỉ kiểm physical size khi archive. SHA đã được actual loader02 kiểm hai lần; không copy hoặc hash lại69MB ở đây.',
        metadata=dict(kind='MAIN60_SIX_GRAPH_CONDITION_BINDING_ENGINEERING', conditions=6, loader_calls=2,
            new_solver_fits=0, neural_model_calls=0, new_independent_N=0, producer_native_files_reference_only=14,
            actual_whole_seconds=final['elapsed_seconds'], prior_failure_preserved=True),
        readme_vi='# Main60 — sáu condition từ Method24 đã fit\n\nBinder02 đạt6condition/2loader,0NN/0solver mới vàJob0. Source/rawfailure01 được giữ. Expert topology28/31 public, predictive stability train48 được bind đúng lineage. 14file69,52MB chỉ tham chiếuSHA. Xem MAIN60_GRAPH_BINDING_READINESS_REPORT01.md để đọc giới hạn và bước MainSelected còn thiếu.\n')


def sakt():
    final = read(PREP/'sakt-selected-fit05/outer-final.json')
    result = read(PREP/'sakt-selected-fit05/result.json')
    check = read(PREP/'sakt-selected-fit05/actual-completion-check.json')
    assert final['status'] == 'ACCEPTED_ACTUAL_SAKT_SELECTED_ONLY_ENGINEERING' and final['errors'] == []
    assert result['source_before'] == result['source_after'] and result['runtime_before'] == result['runtime_after']
    assert check['epochs'] == 6 and check['selected_epoch'] == check['best_saves'] == 1
    assert check['journal_counts']['adam_body_returned'] == 36
    copies = {}
    sources = ['SAKT_SELECTED_ENGINEERING_READINESS_REPORT01.md', 'prepare_selected_archive_inventories01.py',
        'SAKT07_POSITIVE_SELECTED_ENGINEERING_PROPOSAL01.md', 'verify_sakt_selected_cached01.py', 'sakt_selected_cached_comparison01.json',
        'test_sakt_fit_environment_names01.py', 'sakt_environment_names_regression01.log',
        'prepare_sakt_operational_request05.py', 'prepare_sakt_operational_request06.py', 'check_sakt_light_admission05.py',
        'sakt-retry05-light-admission02.json', 'sakt-retry05-root-admission01.json',
        'sakt-positive-materialized-root-check01.json', 'sakt-positive-materialized-root-check02.json', 'sakt-positive-materialized-root-check03.json']
    sources += ['materialize_sakt_selected_positive'+i+'.py' for i in ('01','02','03','04','05')]
    for i in ('01','02','03','04'):
        sources += ['prepare_sakt_selected_positive'+i+'.py', 'run_prepare_sakt_selected_positive'+i+'.py', 'sakt_selected_positive'+i+'_packet.json']
    for i in ('02','03','04','05'):
        sources += ['check_sakt_selected_fit'+i+'.py', 'run_sakt_selected_fit'+i+'.py', 'sakt_selected_fit'+i+'_request.ROOT.json']
    for n in sources: add(copies, n, PREP/n)
    for path in sorted(PREP.iterdir()):
        if path.is_file() and path.name.startswith(('ROOT_SAKT_', 'ROOT_REVIEWED_SAKT_')) and path.suffix == '.md': add(copies, path.name, path)
    for i in ('01','02','03','04'):
        flat(copies, 'sakt-selected-positive-package'+i, 'dry'+i)
        flat(copies, 'sakt-selected-positive-package'+i+'-owned', 'dry_owned'+i)
    for i in ('01','02','03','04','05'): flat(copies, 'sakt-selected-materialization'+i, 'materializer'+i)
    for i in ('02','03','04','05'):
        flat(copies, 'sakt-selected-fit'+i, 'fit'+i)
        flat(copies, 'sakt-selected-fit'+i+'-owned', 'fit_owned'+i)
    flat(copies, 'sakt-selected-operational-request05', 'request05')
    flat(copies, 'sakt-import-closure-fix01', 'package_closure_fix')
    for name in ['src/knowledge_tracing/sakt/research_execution.py','src/knowledge_tracing/sakt/research_runner.py',
                 'tests/sakt/test_research_selected_runner.py','docs/thesis_recovery/30_SAKT_RESEARCH_NUMERICAL_RECIPE_V1.md']:
        add(copies, 'current__'+Path(name).name, ROOT/name)
    for i in ('01','02','03'):
        run_id='sakt-selected-engineering10x84-20261110-'+i
        auth=ROOT/'experiments/sakt/authorizations'/(run_id+'.json')
        add(copies, 'authority_run'+i+'.json', auth)
        directory=ROOT/'experiments/sakt/results'/run_id
        # Chỉ hai thư mục con công khai của output selected, không tìm corpus hoặc TEMP.
        for sub in ('','epoch-1','selection'):
            parent=directory/sub
            if not parent.exists(): continue
            for path in sorted(parent.iterdir()):
                if path.is_file() and path.suffix in {'.json','.jsonl','.csv'}:
                    add(copies, 'native_run'+i+'__'+path.relative_to(directory).as_posix().replace('/','__'), path)
    comparison=read(PREP/'sakt_selected_cached_comparison01.json')
    native_refs=[dict(v, verify_sha_at_archive=True) for v in comparison['checkpoint_binary_refs']]
    reference=refs(['research_tracking/runs/neural-selected-producer-metadata62-20261110-01/manifest.json',
        'research_tracking/runs/sakt-selected-metadata-20261110-01/manifest.json',
        'research_tracking/runs/sakt-research-epoch-engineering-20261109-01/manifest.json',
        'research_tracking/runs/sakt-research-checkpoint-counter-delta-20261109-01/manifest.json',
        'src/knowledge_tracing/evidence.py'])
    return dict(run_id='sakt-selected-engineering-20261110-01', copies=copies, references_sha256=reference,
        native_references=native_refs, original_source_inventory=result['source_before'],
        accepted_outer=(PREP/'sakt-selected-fit05/outer-final.json').relative_to(ROOT).as_posix(),
        accepted_status=final['status'], reference_limit_vi='Hai checkpoint chỉ SHA/size refs và hash physical bytes, không deserialize/copy. Cold62 và component22/33 chỉ tham chiếu bundle đã đóng. Không dựng telemetry đã mất của fit03.',
        metadata=dict(kind='SAKT_ENGINEERING_SELECTED_ONLY_POSITIVE_PUBLIC_PRODUCER', complete_epochs=6, selected_epoch=1,
            accepted_optimizer_steps=36, accepted_train_targets=4032, total_physical_optimizer_steps=72,
            total_physical_train_targets=8064, selection_targets=84, new_independent_N=0,
            actual_whole_seconds=final['elapsed_seconds'], refit=False, calibration=False, public_resume=False, GPU=False),
        readme_vi='# SAKT selected-only engineering đã nghiệm thu\n\nActualfit05 đạt6epochs/best1/36updates4032train-target exposures/full84selection freshreload,source/runtime vàJob0 đạt. Giữ fit02dependencyfail,fit03producerCOMPLETE/wrapperREJECTED vàfit04NO-GO. Tổng72physicalupdates qua hai lượt đã train. Checkpoint binary chỉnativeSHArefs. Xem SAKT_SELECTED_ENGINEERING_READINESS_REPORT01.md. Không Main60/Junyi/fullmatrix/refit/calibration/CUDA hoặc thêm mẫu độc lập.\n')


if __name__ == '__main__':
    save('main60_graph_binding_archive_inputs01.json', main60())
    save('sakt_selected_archive_inputs01.json', sakt())
