"""Hồi quy hai tên local từ AST thật, không import worker hoặc thư viện mô hình."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest


PREP = Path(__file__).resolve().parent


def restoration_projection(filename):
    tree = ast.parse((PREP / filename).read_bytes(), filename=filename)
    main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'main')
    assignments = [node for node in ast.walk(main) if isinstance(node, ast.Assign)]
    environment = next(node for node in assignments if isinstance(node.value, ast.Tuple)
                       and any(isinstance(value, ast.Constant) and value.value == 'TEMP' for value in node.value.elts))
    saved = next(node for node in assignments if any(isinstance(target, ast.Name) and target.id == 'env'
                                                    for target in node.targets))
    export = next(node for node in assignments if isinstance(node.value, ast.Lambda))
    restored = next(node for node in assignments if any(isinstance(target, ast.Name) and target.id == 'restored'
                                                       for target in node.targets))
    expression = restored.value.values[0]
    projection = ast.Module(body=[environment, saved, export,
        ast.Assign(targets=[ast.Name(id='environment_restored', ctx=ast.Store())], value=expression)], type_ignores=[])
    ast.fix_missing_locations(projection)
    return projection, environment.targets[0].id, export.targets[0].id


class EnvironmentNamesRegression(unittest.TestCase):
    def context(self):
        return {'os': SimpleNamespace(environ=dict(TEMP='owned', TMP='owned', TMPDIR='owned', COLUMNS='80', LINES='24'))}

    def test_historical_actual_assignments_reproduce_finally_failure(self):
        projection, environment_name, export_name = restoration_projection('check_sakt_selected_fit03.py')
        self.assertEqual(environment_name, export_name)
        with self.assertRaisesRegex(TypeError, 'not iterable'):
            exec(compile(projection, '<historical-worker-local-projection>', 'exec'), self.context())

    def test_revised_actual_assignments_preserve_environment_check(self):
        projection, environment_name, export_name = restoration_projection('check_sakt_selected_fit04.py')
        self.assertEqual((environment_name, export_name), ('environment_keys', 'export_keys'))
        context = self.context()
        exec(compile(projection, '<revised-worker-local-projection>', 'exec'), context)
        self.assertIs(context['environment_restored'], True)
        self.assertEqual(len(context[environment_name]), 5)
        self.assertTrue(callable(context[export_name]))


if __name__ == '__main__':
    unittest.main()
