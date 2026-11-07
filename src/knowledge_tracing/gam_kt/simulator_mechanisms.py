"""Prototype intervention prerequisite strength, giữ nguyên nguồn lịch sử."""

import ast
import hashlib
import json
import math

from knowledge_tracing.paper2_reference import NOTEBOOK


def build_mechanism_environment(reference, *, prerequisite_strength: float):
    """Chỉ thay coefficient0.55 trong method interact ở class phiên bản riêng.

    Dùng cho unit parity và thiết kế factorial đề xuất. Chưa cấp quyền chạy
    thí nghiệm kết luận hoặc gọi variant này là simulator lịch sử.
    """
    if (isinstance(prerequisite_strength, bool) or not isinstance(prerequisite_strength, (int, float))
            or not math.isfinite(prerequisite_strength) or not 0 <= prerequisite_strength <= 1):
        raise ValueError('invalid prerequisite strength')
    if hashlib.sha256(NOTEBOOK.read_bytes()).hexdigest() != reference['provenance']['notebook_sha256']:
        raise ValueError('reference notebook identity mismatch')
    notebook = json.loads(NOTEBOOK.read_text(encoding='utf-8'))
    methods = []
    for cell in notebook['cells']:
        if cell['cell_type'] == 'code':
            for node in ast.parse(''.join(cell['source'])).body:
                if isinstance(node, ast.ClassDef) and node.name == 'LatentStudentEnvironment':
                    methods.extend(child for child in node.body if isinstance(child, ast.FunctionDef)
                                   and child.name == 'interact')
    if len(methods) != 1:
        raise ValueError('ambiguous environment source')
    method = methods[0]
    assignments = [node for node in ast.walk(method) if isinstance(node, ast.Assign)
                   and any(isinstance(target, ast.Name) and target.id == 'prereq_factor' for target in node.targets)]
    expected = ast.parse('1.0 - 0.55 * prerequisite_deficit', mode='eval').body
    if len(assignments) != 1 or ast.dump(assignments[0].value) != ast.dump(expected):
        raise ValueError('historical prerequisite formula changed')
    coefficient = assignments[0].value.right.left
    assignments[0].value.right.left = ast.copy_location(ast.Name(id='PREREQUISITE_STRENGTH', ctx=ast.Load()), coefficient)
    namespace = {**reference['environment'], 'PREREQUISITE_STRENGTH': float(prerequisite_strength)}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[])),
                 '<Paper2 prerequisite intervention prototype>', 'exec'), namespace)
    return type('ControlledPrerequisiteEnvironment', (reference['environment']['LatentStudentEnvironment'],),
                {'interact': namespace['interact'], 'prerequisite_strength': prerequisite_strength,
                 'environment_id': f'paper2-prerequisite-prototype-lambda-{prerequisite_strength}'})
