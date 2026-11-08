"""Kiểm test đã sửa bằng artifact cũ; không chạy lại fixture train."""
from pathlib import Path
from dataclasses import replace
from types import SimpleNamespace
import hashlib,sys
import torch,pytest

r=Path.cwd();sys.path.insert(0,str(r/'tests/akt'))
import test_simulator_engineering as tests
torch.set_num_threads(2)
def forbidden(*a,**k):raise AssertionError('No model/optimizer/deserialization in stored-artifact regression')
torch.nn.Linear.__init__=forbidden
torch.optim.Adam.__init__=forbidden
tests.engineering.AKTAdapter.__init__=forbidden
torch.load=forbidden
out=r/'artifacts/akt/synthetic/simeng-20261108-complete-7896bb10'
cfg=replace(tests.config('stored-readonly'),output_dir=out,run_id=out.name)
train,selection=tests.toy()
result=SimpleNamespace(checkpoint_sha256=hashlib.sha256((out/'epoch1.pt').read_bytes()).hexdigest())
with pytest.MonkeyPatch.context() as patch:
    tests.test_behavior_dependency_inventory_and_drift_before_deserialize((cfg,train,selection,result),patch)
print('PASS_ONE_CORRECTED_TEST_FUNCTION_STORED_ARTIFACT_NO_TRAIN_NO_LOAD')
