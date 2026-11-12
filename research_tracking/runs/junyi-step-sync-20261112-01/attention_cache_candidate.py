"""Cache hằng số attention theo độ dài và device, giữ checkout gốc."""
import ast
import inspect
import textwrap


def install(adapter):
    namespace = adapter.native.forward.__globals__
    torch = namespace['torch']
    distances = {}
    masks = {}

    def distance(length, device):
        key = (length, device)
        if key not in distances:
            positions = torch.arange(length, device=device)
            distances[key] = (positions[None, :] - positions[:, None]).abs().to(torch.float32)[None, None]
        return distances[key]

    def causal_mask(length, diagonal, device):
        key = (length, diagonal, device)
        if key not in masks:
            masks[key] = torch.ones((1, 1, length, length), dtype=torch.bool, device=device).tril(diagonal=diagonal-1)
        return masks[key]

    namespace['_kltn_distance'] = distance
    namespace['_kltn_causal_mask'] = causal_mask
    tree = ast.parse(inspect.getsource(namespace['attention']))
    function = tree.body[0]
    removed = [node for node in function.body if isinstance(node, ast.Assign)
               and any(isinstance(target, ast.Name) and target.id in ('x1', 'x2') for target in node.targets)]
    assert len(removed) == 2
    function.body = [node for node in function.body if node not in removed]
    replacements = 0
    for node in ast.walk(function):
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'position_effect'
                                              for target in node.targets):
            node.value = ast.parse('_kltn_distance(seqlen, q.device)', mode='eval').body
            replacements += 1
    assert replacements == 1
    ast.fix_missing_locations(tree)
    exec(compile(tree, '<attention-constant-cache-candidate>', 'exec'), namespace)

    layer = namespace['TransformerLayer']
    tree = ast.parse(textwrap.dedent(inspect.getsource(layer.forward)))
    function = tree.body[0]
    removed = [node for node in function.body if isinstance(node, ast.Assign)
               and any(isinstance(target, ast.Name) and target.id == 'nopeek_mask' for target in node.targets)]
    assert len(removed) == 1
    function.body = [node for node in function.body if node not in removed]
    replacements = 0
    for node in ast.walk(function):
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'src_mask'
                                              for target in node.targets):
            node.value = ast.parse('_kltn_causal_mask(seqlen, mask, query.device)', mode='eval').body
            replacements += 1
    assert replacements == 1
    ast.fix_missing_locations(tree)
    temporary = dict(namespace)
    exec(compile(tree, '<causal-mask-cache-candidate>', 'exec'), temporary)
    layer.forward = temporary['forward']
    return dict(cached=['absolute_position_distance', 'causal_mask'], max_length_in_protocol=200,
                upstream_file_modified=False, random_numbers_used=False)
