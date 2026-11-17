"""Kiểm tĩnh bản báo cáo cả bốn lượt numeric đã hoàn tất, chỉ metadata nhỏ."""
import json

from check_a0_update import BUNDLE, Page, REPORT, SOURCE, digest


def check():
    results = [json.loads((SOURCE/f'A{i}_GPU_RESULT01.json').read_text()) for i in range(4)]
    requests = [json.loads((SOURCE/f'REQUEST_A{i}_GPU01.json').read_text()) for i in range(4)]
    for row in results:
        assert row['status'] == 'STAGE_COMMITTED'
        counts = row['result']['counts']
        assert counts['targets'] == counts['fitted_targets'] == 1621484
        assert counts['oov_targets'] == 0 and counts['windows'] == 28653
    for key in ('cache_receipt', 'source_pins', 'source_identity', 'population', 'numeric_budget'):
        assert all(row[key] == requests[0][key] for row in requests), key
    assert [round(row['worker_seconds']) for row in results] == [58, 42, 42, 48]
    assert all(row['full_cohort_approved'] and row['mode'] == 'full' for row in requests)
    cache = json.loads((SOURCE/'CPU_CACHE_RESULT02.json').read_text())['result']
    assert cache['windows']['summary']['learners'] == 15847
    usage = json.loads((SOURCE/'A0_GPU_USAGE_SUMMARY01.json').read_text())
    assert usage['samples'] == 55 and round(usage['mean_utilization_all'], 1) == 6.2
    assert usage['max_utilization'] == 43
    html = (REPORT/'BAO_CAO_NGHIEN_CUU.html').read_text(encoding='utf-8')
    md = (REPORT/'BAO_CAO.md').read_text(encoding='utf-8')
    page = Page()
    page.feed(html)
    page.close()
    assert not page.stack and len(page.ids) == len(set(page.ids))
    assert set(page.anchors) <= set(page.ids)
    prose = ' '.join(page.prose)
    phrases = ('cả A0–A3 đã tính đủ dự báo', '1.621.484', '15.847', '10% người học', 'fold4',
        '58 giây', '42/42/48 giây', '6,88 giây', '6,2%', '43%', 'mốc 50% chưa đạt',
        'chưa có kết quả nghiệm thu', 'đánh giá độc lập', 'Benchmark BKT/GAM-KT qua 5 phép chia')
    for phrase in phrases:
        assert phrase in md and phrase in prose, phrase
    assert html.count('<svg ') == 1
    figure = BUNDLE.parents[2]/'research_tracking/runs/rq12-existing-evidence-20261117-01/rq1-ready-preview-v01.svg'
    status = dict(status='PASS_ALL_FOUR_CALIBRATION_NUMERIC_STATIC_REPORT', checks=list(phrases),
        targets_per_model=1621484, learners=15847, models=['A0','A1','A2','A3'],
        worker_seconds=[row['worker_seconds'] for row in results], same_data_and_execution_binding=True,
        calibration_fit_accepted=False, independent_comparison_completed=False,
        browser_visual_tested=False, figure_modified=False, figure_sha256=digest(figure))
    output = BUNDLE/'QA05.json'
    if output.exists():
        assert json.loads(output.read_text()) == status
    else:
        with output.open('x', encoding='utf-8') as stream:
            json.dump(status, stream, ensure_ascii=False, indent=2)
    print('PASS — four complete numeric runs, matching input binding, report claims and HTML structure')


if __name__ == '__main__':
    check()
