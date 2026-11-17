"""Kiểm bản thảo theo nguồn nghiệm thu đã lưu, không thực nghiệm mới."""
from pathlib import Path
import hashlib
import json
import re
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).resolve().parent
DRAFT = ROOT/'research_tracking/reports/THESIS_RESULTS_DISCUSSION_DRAFT_20261117.md'
CALIBRATION = ROOT/'research_tracking/runs/junyi-calibration-real-20261117-01'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def main():
    text = DRAFT.read_text(encoding='utf-8')
    visible = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', text)
    words = len(visible.split())
    assert 1500 <= words <= 2500
    links = re.findall(r'\]\(([^)]+)\)', text)
    sources = {(DRAFT.parent/unquote(link)).resolve() for link in links}
    assert all(path.is_file() for path in sources)
    model_rows = [line for line in text.splitlines() if line.startswith(('| Grade10 A', '| Junyi A'))]
    assert len(model_rows) == 11
    assert len([line for line in model_rows if line.startswith('| Grade10')]) == 7
    assert len([line for line in model_rows if line.startswith('| Junyi')]) == 4
    acceptance = read(CALIBRATION/'POSTSTOP_CALIBRATION_METADATA_ACCEPTANCE01.json')
    assert acceptance['status'] == 'A0_A1_CALIBRATION_METADATA_AND_FROZEN_PARTITIONS_VERIFIED'
    for variant in acceptance['variants']:
        assert variant['five_artifacts_verified']
        assert variant['independent_evaluation'] is False
        temperature = read(CALIBRATION/f"{variant['variant']}_CALIBRATION_TEMPERATURE01.json")
        sources.add(CALIBRATION/f"{variant['variant']}_CALIBRATION_TEMPERATURE01.json")
        assert temperature['total_targets'] == 1621484
        for key, decimals in [('temperature', 5), ('raw_log_loss', 6), ('calibrated_log_loss', 6)]:
            assert temperature[key] == variant[key]
            assert f'{variant[key]:.{decimals}f}'.replace('.', ',') in text
    gpu = read(CALIBRATION/'GPU_OUTPUT_ACCEPTANCE01.json')
    assert [row['variant'] for row in gpu['variants']] == ['A0', 'A1', 'A2', 'A3']
    assert all(row['targets'] == 1621484 for row in gpu['variants'])
    statistics = read(ROOT/'research_tracking/runs/paper2-statistical-reproduction-20261117-02/attempt01/RESULT.json')
    assert statistics['hypotheses'] == 117 and statistics['holm_rejection_mismatches'] == 0
    assert all(value == 117 for value in statistics['exact_equal_hypotheses'].values())
    sources.update([ROOT/'research_tracking/runs/modal-akt-recovery-20261112-01/main60-a0-verification.json',
                    ROOT/'research_tracking/runs/modal-akt-graph-selected-20261112-01/batch-summary.json'])
    a0 = read(ROOT/'research_tracking/runs/modal-akt-recovery-20261112-01/main60-a0-verification.json')
    graph = read(ROOT/'research_tracking/runs/modal-akt-graph-selected-20261112-01/batch-summary.json')
    assert a0['selected_epoch'] == 5 and a0['prediction_rows'] == 1260
    for condition in graph['conditions']:
        expected = 5 if condition['candidate_id'] == 'A1_EXPERT' else 4
        assert condition['selected_epoch'] == expected
    pins = []
    for path in sorted(sources):
        raw = path.read_bytes()
        pins.append(dict(path=path.relative_to(ROOT).as_posix(), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))
    (BUNDLE/'SOURCES.json').write_text(json.dumps(pins, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    qa = dict(status='PASS', visible_word_count=words, local_links=len(links), missing_links=0,
              model_rows=len(model_rows), sources=len(pins), new_experiments=0,
              calibration_targets=1621484, independent_evaluation=False,
              limits=['Draft academic chapter; no completed RQ/sprint claim',
                      'Paper2 statistics reproduced from saved seed outcomes, not trajectories',
                      'Historical library versions incompletely pinned; current environment exact',
                      'A0/A1 LL evaluated on own temperature-fit cohort',
                      'A2/A3 temperature and independent evaluation pending'])
    (BUNDLE/'QA.json').write_text(json.dumps(qa, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(qa, ensure_ascii=False))


if __name__ == '__main__':
    main()
