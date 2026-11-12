"""Candidate chỉ đổi cast ma trận khoảng cách, không sửa checkout upstream."""
import ast
import inspect


def install(adapter):
    namespace = adapter.native.forward.__globals__
    reference = namespace['attention']
    tree = ast.parse(inspect.getsource(reference))
    function = tree.body[0]
    assignments = [node for node in ast.walk(function) if isinstance(node, ast.Assign)
                   and any(isinstance(target, ast.Name) and target.id == 'position_effect'
                           for target in node.targets)]
    assert len(assignments) == 1
    assignment = assignments[0]
    expected = ast.parse(
        '(torch.abs(x1-x2)[None, None, :, :].type(torch.FloatTensor).to(device))',
        mode='eval').body
    assert ast.dump(assignment.value) == ast.dump(expected), 'Pinned distance expression changed'
    distance = assignment.value.func.value.func.value
    assignment.value = ast.Call(func=ast.Attribute(value=distance, attr='to', ctx=ast.Load()),
                                args=[], keywords=[ast.keyword(arg='dtype', value=ast.Attribute(
                                    value=ast.Name(id='torch', ctx=ast.Load()), attr='float32', ctx=ast.Load()))])
    ast.fix_missing_locations(tree)
    exec(compile(tree, '<attention-device-cast-candidate>', 'exec'), namespace)
    assert namespace['attention'] is not reference
    return dict(changed_expression='position_effect cast only',
                previous='GPU int64 → CPU float32 → GPU float32',
                candidate='GPU int64 → GPU float32', upstream_file_modified=False)
