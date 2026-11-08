"""Chuẩn bị bundle hậu kiểm cache; không chạy lại phép phân tích hoặc model."""
from pathlib import Path
import archive_edge_artifact_cross_ready01 as base

ROOT, PREP = base.ROOT, base.PREP
RUN_ID = 'rq1-cross-ready-membership-20261109-01'
OLD = ROOT/'research_tracking/runs/rq1-fixed-edge-set-contrast-20261108-01'
REPORT = ROOT/'research_tracking/reports/rq1_cross_ready_membership_20261109.md'
SOURCE = 'scripts/research/analyze_rq1_cross_ready.py'
SOURCE_SHA = '423968f864c84c8fc66a6678bf9351b195cc3ce47d38eb8696ddbab0ee830398'
PLAN_SHA = 'f54f99fa4cf098ae28bc4488bd827b9bca1b05663472189364618228e4b43fc8'


def verify():
    need, read, sha = base.need, base.read, base.sha
    plan = read(PREP/'rq1_cross_ready_plan01.json')
    need(sha(ROOT/SOURCE) == SOURCE_SHA and sha(PREP/'rq1_cross_ready_plan01.json') == PLAN_SHA, 'executed source/plan')
    references = {(OLD/n).relative_to(ROOT).as_posix(): h for n,h in plan['inputs_sha256'].items()}
    need(len(references) == 5, 'exact5 old pointers')
    for name, pin in references.items():
        need(sha(ROOT/name) == pin, 'immutable old input SHA')
    manifest = read(OLD/'manifest.json')
    need(manifest['status'] == 'completed' and all(manifest['outputs_sha256'].get(n) == h
         for n,h in plan['inputs_sha256'].items() if n != 'manifest.json'), 'old source manifest output binding')
    for name in ('historical_runner.py', 'observer.py'):
        need(manifest['outputs_sha256'].get(name) == sha(OLD/name), 'historical timing source binding')
    inner = PREP/'rq1-cross-ready-attempt01'; owner = PREP/'rq1-cross-ready01-owned'
    need({p.name for p in inner.iterdir()} == {'summary.json','event_flags.json','validation.json','result.json'}
         and not (owner/'postwrite_rejection.json').exists(), 'no partial/late failure')
    result, validation, final, summary = (read(p) for p in (inner/'result.json',inner/'validation.json',owner/'final.json',inner/'summary.json'))
    need(final['status'] == 'ACCEPTED_CACHED_CROSS_READY_DIAGNOSTIC' and final['errors'] == []
         and base.finite(final['elapsed_seconds'],10) and final['cap_seconds'] == 10, 'accepted cached caller')
    need(final['input_before'] == final['input_after'] == plan['inputs_sha256']
         and final['source_sha256'] == SOURCE_SHA and final['plan_sha256'] == PLAN_SHA, 'caller source/input binding')
    for name, item in final['artifacts'].items():
        need(name in {'summary.json','event_flags.json','validation.json','result.json'} and sha(inner/name) == item['sha256']
             and (inner/name).stat().st_size == item['bytes'], 'actual output SHA/size')
    need(set(final['artifacts']) == {'summary.json','event_flags.json','validation.json','result.json'}, 'exact4 caller artifacts')
    need(result['status'] == 'INNER_COMPLETE_PENDING_OWNED_OUTER_ACCEPTANCE' and base.finite(result['worker_seconds'],7)
         and result['outputs_sha256'] == {n:v['sha256'] for n,v in final['artifacts'].items() if n != 'result.json'}, 'inner pending receipt')
    need(validation['rows'] == 1080 and validation['raw_rows_per_stream'] == 3240 and validation['groups'] == 16
         and validation['joint_cells'] == 128 and validation['membership_cells'] == 256
         and all(validation[k] is True for k in ('exact_query_label_key_join','old_per_event_flags_exact','old_marginals_exact',
             'own_preview_in_own_R_not_required','no_dropped_rows')) and validation['inputs_sha256'] == plan['inputs_sha256']
         and validation['source_sha256'] == SOURCE_SHA and validation['plan_sha256'] == PLAN_SHA, 'complete validated1080 population')
    need(all(type(final[k]) is int and final[k] == 0 for k in ('new_independent_N','model_calls','solver_fits'))
         and validation['new_independent_N'] == validation['actual_model_calls'] == 0, 'zero new native/N')
    receipt = base.owned(owner)
    need(receipt['worker_sha256'] == SOURCE_SHA and base.finite(receipt['elapsed_seconds'],10)
         and receipt['cleanup_reserve_seconds'] == 2, 'cached owned allocation/source')
    need(len(summary['groups']) == 16 and summary['groups'][0]['group'] == 'pooled', 'all16 stored groups')
    pooled = summary['groups'][0]
    need({r['signature']:r['count'] for r in pooled['joint_MRA_cells']} ==
         {'000':973,'001':17,'010':0,'011':0,'100':30,'101':0,'110':55,'111':5}, 'reviewed pooled table')
    need({r['signature']:r['count'] for r in pooled['membership_cells'] if r['count']} == {'1101':5,'1111':1075}
         and pooled['own_R_limited_snapshots'] == 0, 'reviewed own/cross membership')
    references.update({SOURCE: SOURCE_SHA, base.HELPER:sha(ROOT/base.HELPER)})
    return dict(kind='POST_HOC_FIXED_STREAM_RECORDED_READY_MEMBERSHIP_NOT_SCORE_ONLY', rows=1080,groups=16,
        source_sha256=SOURCE_SHA,plan_sha256=PLAN_SHA,new_independent_N=0,model_calls=0,solver_fits=0,
        caller_prewrite_elapsed_seconds=final['elapsed_seconds'],cap_seconds=10,owned_cleanup=True,
        joint_R_change_preview_unchanged=55,preview_change_M_R_unchanged=17,joint_M_R_preview_changed=5,
        own_R_true_observed_not_universal=True,original_gzip_copied=False), references


def selections():
    pairs = [(ROOT/SOURCE,'analyze_rq1_cross_ready.py'), (PREP/'rq1_cross_ready_plan01.json','plan.json'),
        (PREP/'run_rq1_cross_ready01.py','root_outer.py'),
        (ROOT/'scripts/research/windows_owned_worker.py','windows_owned_worker.py'),
        (ROOT/base.HELPER,'evidence_helper.py'),(Path(__file__).resolve(),'archive_rq1_cross_ready01.py')]
    pairs += [(PREP/'rq1-cross-ready-attempt01'/n,n) for n in ('summary.json','event_flags.json','validation.json','result.json')]
    pairs += [(PREP/'rq1-cross-ready01-owned'/n,'owned__'+n) for n in base.OWNED_FILES]
    pairs.append((PREP/'edge-artifact-cross-ready02-owned/final.json','pure60_prerequisite_terminal.json'))
    # Opaque timing evidence only; do not import the historical selector or run it.
    pairs += [(OLD/'historical_runner.py','historical_runner.py'),(OLD/'observer.py','historical_observer.py')]
    return pairs


def note():
    return '''# RQ1 — cross-ready membership trên fixed stream

Hậu kiểm stdlib cache đã nghiệm thu:1080cặp query/y chung,16groups,128MRAcells+256membershipcells kể cả0. Không tạo thêm người học/quỹ đạo/model: newN0. Không copy gzip gốc;5SHA nguồn nằm source_references.json, thuộc ../rq1-fixed-edge-set-contrast-20261108-01/.

55cặp Rđổi/fullpreviewgiữ;17previewđổi M/Rgiữ;5jointchanges có fullwinner ngoài emptyR, emptywinner trong fullR. Đây membership của recordedR, không actualC/B, không score-only/causal mediation hoặc learningbenefit. Preview không served. OwnRtrue trong mẫu đã qua historicalassertion; không invariant source universal. Report canonical ../../reports/rq1_cross_ready_membership_20261109.md; report_snapshot.md giữ bytes và linkrelative gốc của canonical vị trí, không sửa provenance.

Native lịch sử predict(original)→select(deepcopy)→recordR/S/M(original)→update/loggeditembookkeeping. Không suy ranking từ R khi C/B chưa logged. Fixed-stream historical runner gốc đã truy được Git e4e6a262bddcdd3b6b6de8c1115ef0eb54b3240a; C13 xác nhận exact legacy parity giữa observed/control/historical. Hạn chế original-source-missing của nhánh closed-loop khác không áp dụng ở đây. Tất cả16groups và mọi zero cells giữ trong summary/eventflags.

execution.log là log archiver; owned stdout/stderr, final/receipt và root_outer.py là proof dispatch riêng. SHA nguồn và copy trước/sau kiểm lại; verify_evidence_bundle chỉ integrity. Không fit/model/teacher/network/newdata hoặc Gitmutation. Optional review files chỉ copy nguyên bytes, không tự suy PASS.
'''


if __name__ == '__main__':
    base.entry(RUN_ID, verify, selections, note, required_report=REPORT)
