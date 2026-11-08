"""Offline AST-extracted env function; no driver/project/remote execution."""
import ast
from pathlib import Path
import types
import unittest

P=Path(__file__).with_name('linux_cpu_validation_driver02.py')
TREE=ast.parse(P.read_text())
NODE=next(n for n in TREE.body if isinstance(n,ast.FunctionDef) and n.name=='isolated_git_environment')
UPSTREAM=Path('/content/KLTN_GPU08_20261108_01/artifacts/akt/dependencies/upstream')
ENV={'os':types.SimpleNamespace(devnull='/dev/null'),'UPSTREAM':UPSTREAM}
exec(compile(ast.Module(body=[NODE],type_ignores=[]),str(P),'exec'),ENV)
ISOLATE=ENV['isolated_git_environment']


class GitEnvironment(unittest.TestCase):
    def test_routing_config_and_command_injection_variables_removed(self):
        bad={k:'sensitive-fixture' for k in ('GIT_DIR','GIT_WORK_TREE','GIT_OBJECT_DIRECTORY','GIT_ALTERNATE_OBJECT_DIRECTORIES','GIT_CONFIG_SYSTEM','GIT_CONFIG_PARAMETERS','GIT_CONFIG_KEY_99','GIT_CONFIG_VALUE_99','GIT_CONFIG','GIT_SSH_COMMAND','GIT_ASKPASS','git_dir')}
        self.assertTrue(set(bad).isdisjoint(ISOLATE(bad)))
    def test_gh_credentials_removed(self):
        bad={k:'sensitive-fixture' for k in ('GH_TOKEN','GH_HOST','GITHUB_TOKEN','GITHUB_API_URL','SSH_AUTH_SOCK','AWS_SECRET_ACCESS_KEY','HTTPS_PROXY','AUTH_HEADER','api_key','NETRC','CURL_HOME','LD_PRELOAD','LD_LIBRARY_PATH')}
        self.assertTrue(set(bad).isdisjoint(ISOLATE(bad)))
    def test_required_protocol_and_config_guards_override_poisoned_inputs(self):
        expected={'GIT_ALLOW_PROTOCOL':'__NO_TRANSPORT__','GIT_OPTIONAL_LOCKS':'0','GIT_NO_LAZY_FETCH':'1','GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null','GIT_TERMINAL_PROMPT':'0','GIT_CONFIG_COUNT':'5','PATH':'/usr/bin:/bin'}
        result=ISOLATE({k:'poisoned' for k in expected})
        self.assertEqual({k:result[k] for k in expected},expected)
    def test_exact_safe_directory_and_no_wildcard(self):
        out=ISOLATE({});self.assertEqual(out['GIT_CONFIG_KEY_0'],'safe.directory');self.assertEqual(out['GIT_CONFIG_VALUE_0'],UPSTREAM.as_posix());self.assertNotIn('*',out['GIT_CONFIG_VALUE_0'])
    def test_hooks_autocrlf_and_credential_helpers_disabled(self):
        out=ISOLATE({});pairs={out[f'GIT_CONFIG_KEY_{i}']:out[f'GIT_CONFIG_VALUE_{i}'] for i in range(5)}
        self.assertEqual(pairs,{'safe.directory':UPSTREAM.as_posix(),'core.hooksPath':'/dev/null','core.autocrlf':'false','credential.helper':'','credential.interactive':'false'})
    def test_unrelated_environment_retained_and_input_not_mutated(self):
        original={'LANG':'C.UTF-8','CUDA_VISIBLE_DEVICES':'','OMP_NUM_THREADS':'2','GIT_DIR':'bad'};snapshot=dict(original)
        result=ISOLATE(original);self.assertEqual(original,snapshot)
        self.assertEqual({k:result[k] for k in ('LANG','CUDA_VISIBLE_DEVICES','OMP_NUM_THREADS')},{k:original[k] for k in ('LANG','CUDA_VISIBLE_DEVICES','OMP_NUM_THREADS')})
    def test_phase02_names_and_existing_native_runid_preserved(self):
        text=P.read_text();self.assertIn("ROOT/'linux_cpu_validation_driver02.py'",text)
        self.assertIn('linux-cpu-validation-runtime-20261108-02/result.json',text);self.assertIn('linux-cpu-20261108-02.json',text)
        self.assertIn("RUN_ID='20261108-linux-native-23'",text);self.assertIn("'--timeout-seconds','600'",text)
    def test_isolation_called_before_Popen(self):
        text=P.read_text();self.assertLess(text.index('env=isolated_git_environment(env)'),text.index('process=subprocess.Popen'))
        self.assertIn("env['XDG_CONFIG_HOME']=str(directory/'home')",text)


if __name__=='__main__':unittest.main(verbosity=2)
