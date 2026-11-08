import importlib.util,json,unittest
from pathlib import Path
w=Path(__file__).resolve().parent.parent
suite=unittest.TestSuite()
for index,name in enumerate(('test_hidden_audit01.py','test_startup_origin02.py')):
 spec=importlib.util.spec_from_file_location('combined_current_'+str(index),w/name)
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
result=unittest.TextTestRunner(verbosity=2).run(suite)
print(json.dumps({'unit_methods':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'actual_target_normalstartup_model_GPU_calls':0,'scope':'Both testmodules loaded against same current source bytes; metadata/AST/mocks only.'}))
raise SystemExit(0 if result.wasSuccessful() else 1)
