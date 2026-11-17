"""Trích source/config notebook đã kiểm thành payload terminal không secrets."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def main():
    notebook = json.loads((ROOT/'notebooks/akt_colab_response_calibration_cpu.ipynb').read_text(encoding='utf-8'))
    values,upstream = {},None
    for cell in notebook['cells']:
        if cell['cell_type'] != 'code':
            continue
        tree = ast.parse(''.join(cell['source']))
        for node in ast.walk(tree):
            if isinstance(node,ast.Assign):
                for target in node.targets:
                    if isinstance(target,ast.Name) and target.id in ('FILES','PAYLOAD'):
                        values[target.id] = ast.literal_eval(node.value)
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr == 'b64decode':
                if isinstance(node.args[0],ast.Constant):
                    upstream = node.args[0].value
    assert set(values) == {'FILES','PAYLOAD'} and upstream
    for name,text in values['FILES'].items():
        assert text == (ROOT/'scripts/akt'/name).read_text(encoding='utf-8')
    payload = dict(files=values['FILES'],plan=values['PAYLOAD'],upstream_b64=upstream)
    raw = json.dumps(payload,ensure_ascii=False,separators=(',',':')).encode()
    destination = HERE/'PAYLOAD.json'
    destination.write_bytes(raw)
    receipt = dict(path=destination.relative_to(ROOT).as_posix(),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    (HERE/'PAYLOAD_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
