"""Train boundary, chronology và first exposure counts cho order diagnostic."""

import pytest

from knowledge_tracing.gam_kt.practice_order import summarize_practice_order


def rows():
    return [{'user_id': 'u', 'exercise': exercise, 'partition': 'development', 'fold': 1,
             'time_done': index, 'source_row': index} for index, exercise in enumerate(['B','A','B'], 1)]


def test_first_exposure_is_counted_once_and_no_labels_are_needed():
    result = summarize_practice_order(rows(), [('A','B')], allowed_users={'u'}, outer_fold=0)
    assert result['events'] == 3
    assert result['edges'][0]['child_first_count'] == 1
    assert result['edges'][0]['parent_first_fraction'] == 0


@pytest.mark.parametrize('field,value', [('partition','test'), ('fold',0), ('user_id','outside')])
def test_order_diagnostic_rejects_outside_training_scope(field, value):
    data = rows()
    data[0][field] = value
    with pytest.raises(ValueError, match='scope'):
        summarize_practice_order(data, [('A','B')], allowed_users={'u'}, outer_fold=0)


def test_order_diagnostic_rejects_out_of_order_rows_and_over_budget():
    with pytest.raises(ValueError, match='chronology'):
        summarize_practice_order(rows()[::-1], [('A','B')], allowed_users={'u'}, outer_fold=0)
    with pytest.raises(ValueError, match='cap'):
        summarize_practice_order(rows(), [('A','B')], allowed_users={'u'}, outer_fold=0,max_events=2)
