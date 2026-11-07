"""Kiểm phép tái dựng dùng source SCC rule trên fixture có cạnh đi ra SCC."""

from knowledge_tracing.gam_kt.catalog_graph import correct_with_historical_rule


def test_historical_scc_rule_keeps_cross_component_edges_and_isolated_nodes():
    result = correct_with_historical_rule(['A','B','C','D','Z'],[('A','B'),('B','C'),('C','A'),('C','D')])
    assert result['corrected_edges'] == [('C','D')]
    assert result['removed_edges'] == [('A','B'),('B','C'),('C','A')]
    assert result['nodes'] == ['A','B','C','D','Z']
    assert result['corrected_is_DAG'] is True
