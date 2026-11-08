import importlib.util,json,unittest
from pathlib import Path
w=Path(__file__).resolve().parent.parent;suite=unittest.TestSuite()
for index,name in enumerate(('test_hidden_audit01.py','test_startup_origin02.py','test_reserve04.py')):
 spec=importlib.util.spec_from_file_location('current20_'+str(index),w/name);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
r=unittest.TextTestRunner(verbosity=2).run(suite)
print(json.dumps({'unit_methods':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'actual_target_model_GPU_calls':0}))
raise SystemExit(0 if r.wasSuccessful() else 1)
