import ast
import hashlib
import json
from pathlib import Path

import pytest


def inventory_function():
    source = Path('research_tracking/runs/junyi-calibration-real-20261117-01/archive_colab_a2_partial02.py')
    tree = ast.parse(source.read_text(encoding='utf-8'))
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'inventory_raw')
    namespace = {'Path':Path, 'hashlib':hashlib}
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(source), 'exec'), namespace)
    return namespace['inventory_raw']


def test_native_partial_manifest_without_shard_hashes(tmp_path):
    manifest = {'shards':[{'path':'part-00000.parquet','rows':2,'user_id':'synthetic'}]}
    (tmp_path/'manifest.json').write_text(json.dumps(manifest))
    (tmp_path/'part-00000.parquet').write_bytes(b'synthetic-parquet-bytes')
    result = inventory_function()(tmp_path, manifest)
    assert result['part-00000.parquet']['sha256'] == hashlib.sha256(b'synthetic-parquet-bytes').hexdigest()
    assert set(result) == {'manifest.json','part-00000.parquet'}


def test_partial_manifest_existing_bad_hash_is_rejected(tmp_path):
    manifest = {'shards':[{'path':'part-00000.parquet','sha256':'0'*64}]}
    (tmp_path/'manifest.json').write_text(json.dumps(manifest))
    (tmp_path/'part-00000.parquet').write_bytes(b'synthetic-parquet-bytes')
    with pytest.raises(ValueError, match='SHA'):
        inventory_function()(tmp_path, manifest)
