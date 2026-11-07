"""Đối chiếu loader upstream bằng dữ liệu tổng hợp, không đọc dataset thật."""

import importlib.util
from pathlib import Path

import numpy as np

from knowledge_tracing.akt.encoding import fit_vocabulary
from knowledge_tracing.akt.tensors import collate_windows
from knowledge_tracing.akt.types import KTEvent, LearnerEvents
from knowledge_tracing.akt.windows import iter_windows


def upstream_loader():
    path = Path('artifacts/akt/dependencies/upstream/load_data.py')
    spec = importlib.util.spec_from_file_location('reference_akt_data', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_three_line_loader_encoding_padding_and_student_indices(tmp_path):
    fixture = tmp_path / 'synthetic.csv'
    fixture.write_text('891,78276\n1,2,1,3,2\n1,0,1,0,1\n', encoding='utf-8')
    q, qa, student_indices = upstream_loader().DATA(3, 8, ',').load_data(fixture)
    np.testing.assert_array_equal(q, [[1, 2, 1, 3, 2, 0, 0, 0]])
    np.testing.assert_array_equal(qa, [[4, 2, 4, 3, 5, 0, 0, 0]])
    np.testing.assert_array_equal(student_indices, [0])
    np.testing.assert_array_equal(np.floor((qa[0, :5] - 1) / 3), [1, 0, 1, 0, 1])


def test_four_line_loader_separates_skill_and_problem_ids(tmp_path):
    fixture = tmp_path / 'synthetic_pid.csv'
    fixture.write_text('891,78276\n11,12,11\n1,2,1\n1,0,1\n', encoding='utf-8')
    q, qa, pid = upstream_loader().PID_DATA(3, 4, ',').load_data(fixture)
    np.testing.assert_array_equal(q, [[1, 2, 1, 0]])
    np.testing.assert_array_equal(qa, [[4, 2, 4, 0]])
    np.testing.assert_array_equal(pid, [[11, 12, 11, 0]])


def test_header_values_do_not_control_loader_output(tmp_path):
    loader = upstream_loader().DATA(3, 4, ',')
    first = tmp_path / 'first.csv'
    second = tmp_path / 'second.csv'
    first.write_text('891,78276\n1,2\n1,0\n', encoding='utf-8')
    second.write_text('arbitrary header\n1,2\n1,0\n', encoding='utf-8')
    for original, changed in zip(loader.load_data(first), loader.load_data(second)):
        np.testing.assert_array_equal(original, changed)


def test_kltn_reconstructs_native_alignment_without_double_shift(tmp_path):
    fixture = tmp_path / 'synthetic.csv'
    fixture.write_text('unused\n1,2,3\n1,0,1\n', encoding='utf-8')
    q, qa, _ = upstream_loader().DATA(3, 3, ',').load_data(fixture)
    learner = LearnerEvents('synthetic', 0, tuple(
        KTEvent('synthetic', exercise, index, index, response, 0, 0)
        for index, (exercise, response) in enumerate(zip(['A', 'B', 'C'], [1, 0, 1]))
    ))
    vocabulary = fit_vocabulary([learner])
    windows = list(iter_windows(learner, vocabulary, training=False))
    batch = collate_windows(windows, n_items=3, device='cpu')
    np.testing.assert_array_equal(batch.q_data.numpy(), q)
    np.testing.assert_array_equal(batch.qa_data.numpy()[:, :-1], qa[:, :-1])
    # Đáp án cuối chưa quan sát được dùng placeholder và bị strict-past mask loại.
    assert batch.qa_data[0, -1].item() == 3
    assert qa[0, -1] == 6
