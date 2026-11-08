"""3guard cases stdlib only; no native imports/Git/model/worker execution."""
import ast
import copy
import importlib.util
import json
import os
from pathlib import Path
import unittest

WORK=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('dummy_driver_guard_tests',WORK/'linux_cpu_dummy_worker_driver02.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
FIXTURES=WORK.parents[3]/'artifacts/akt/local-tests/dummy-worker02-acceptance-fix-20261108-01'/os.environ['DUMMY_GUARD_FIXTURE_NAME']

def config():
    return {**module.CAPS,'phase':'smoke','device':'cpu','graph':False,'n_pid':0,'d_model':32,'heads':4,
            'blocks':1,'d_ff':64,'final_fc':32,'dropout':0.0,'batch_size':4,'max_epochs':1,'context':100,
            'target_block':100,'max_length':200,'run_id':module.DATASET,'partition':'development','project_root':'.',
            'output_dir':'experiments/akt/results/'+module.DATASET,'source_root':'artifacts/akt/dependencies/upstream',
            'execution_enabled':False,'recovery':None,'max_total_targets':128}

class Guards(unittest.TestCase):
    def test_alias_copy_conflict_and_bad_source_sha_no_overwrite(self):
        FIXTURES.mkdir(parents=True,exist_ok=False)
        source=FIXTURES/'runtime.json';source.write_bytes(b'{"device":"cpu"}\n');destination=FIXTURES/'alias/runtime.json'
        with self.assertRaises(ValueError):module.exclusive_alias_copy(source,destination,'0'*64,Path.read_bytes)
        self.assertFalse(destination.exists())
        digest=module.sha(source.read_bytes());receipt=module.exclusive_alias_copy(source,destination,digest,Path.read_bytes)
        self.assertEqual(source.read_bytes(),destination.read_bytes());self.assertEqual(receipt['source_sha256_after'],digest)
        with self.assertRaises(FileExistsError):module.exclusive_alias_copy(source,destination,digest,Path.read_bytes)
        # Execute ONLY the generated JSON writer definition, not native binding child.
        child=ast.parse(module.BIND_CHILD)
        writer=next(n for n in child.body if isinstance(n,ast.FunctionDef) and n.name=='w')
        namespace={'json':json};exec(compile(ast.Module(body=[writer],type_ignores=[]),'child-json-writer','exec'),namespace)
        target=FIXTURES/'proposal.json';namespace['w'](target,{'approved':False})
        self.assertEqual(json.loads(target.read_bytes()),{'approved':False})

    def test_explicit_context_config_and_all_pin_shapes_failclosed(self):
        original=config();result=module.execution_config(original)
        self.assertIs(original['execution_enabled'],False);self.assertIs(result['execution_enabled'],True)
        for changes in ({'graph':True},{'max_steps':3},{'recovery':{}},{'max_wall_seconds':True}):
            with self.assertRaises(ValueError):module.execution_config({**original,**changes})
        for value in (*module.PINS.values(),module.GATE_HELPER_SHA,module.VALIDATOR_SHA):module.validate_sha(value)
        with self.assertRaises(ValueError):module.validate_sha('a'*65)
        with self.assertRaises(ValueError):module.context_command('smoke',Path('c'),None,Path('ctx'),'a'*64)
        with self.assertRaises(ValueError):module.context_command('preflight',Path('c'),None,None,'a'*64)
        reference='USER_ENGINEERING_NO_MODEL_FIT_WITH_MODE'
        legacy=(module.BIND_CHILD.replace('CAPS_NAMES',repr(tuple(module.CAPS))).replace('CONTEXT_SHA',repr('a'*64))
                .replace('EXECUTION_REFERENCE',repr(reference)).replace('MODE',repr('execute')))
        with self.assertRaises(SyntaxError):ast.parse(legacy)
        ast.parse(module.binding_child_code('execute','a'*64,reference))
        for phase in ('preflight','smoke'):
            command=module.context_command(phase,Path('c'),Path('auth'),Path('ctx'),'a'*64)
            self.assertIn('--context-file',command);self.assertIn('--context-sha256',command)
            self.assertIn('knowledge_tracing.akt.cli',command);self.assertNotIn('_execute',command)

    def test_completion_rejects_zero_updates_wrong_context_and_fake_ancestry(self):
        context='a'*64;binding={'config_sha256':'b'*64,'identity':{'worker_context_sha256':context,'build_hashes':{'fixture.py':'d'*64},'gate2_report_sha256':'e'*64,'gate2_test_log_sha256':'f'*64,'gate2_pointer_sha256':'0'*64}}
        manifest={'status':'completed','phase':'smoke','run_id':module.DATASET,'approved_caps':module.CAPS,
            'authorized_config_sha256':'b'*64,'identity':{'worker_context_sha256':context},
            'gate_records':{'gate2':{'status':'PASS','report_sha256':'e'*64,'test_log_sha256':'f'*64,'pointer_sha256':'0'*64}},
            'summary':{'training':{'optimizer_steps':2,'valid_targets':48,'nonzero_gradient_steps':2,'parameter_update_steps':2},
                'coverage':{'prediction_rows':8,'expected_rows':8},'checkpoint_reload_state_exact':True,
                'outer_users_requested':False,'holdout_requested':False}}
        resources={'status':'completed','phase':'smoke','run_id':module.DATASET,'worker_returncode':0,'worker_pid':202,
            'elapsed_seconds':2.5,'parent_events':[{'event':'watchdog-after-worker-spawn','pid':101,'worker_pid':202}]}
        module.validate_completion(manifest,resources,binding,context,101)
        wrong_gate=copy.deepcopy(manifest);wrong_gate['gate_records']['gate2']['test_log_sha256']='c'*64
        with self.assertRaises(ValueError):module.validate_completion(wrong_gate,resources,binding,context,101)
        for field,value in [('nonzero_gradient_steps',0),('parameter_update_steps',0)]:
            mutant=copy.deepcopy(manifest);mutant['summary']['training'][field]=value
            with self.assertRaises(ValueError):module.validate_completion(mutant,resources,binding,context,101)
        with self.assertRaises(ValueError):module.validate_completion(manifest,resources,binding,'c'*64,101)
        with self.assertRaises(ValueError):module.validate_completion(manifest,{**resources,'worker_pid':101},binding,context,101)

if __name__=='__main__':unittest.main(verbosity=2)
