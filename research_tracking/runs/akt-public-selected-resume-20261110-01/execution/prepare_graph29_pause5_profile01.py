"""Đổi bindings của launcher đã kiểm sang parent pause5 có scope riêng."""
from pathlib import Path
import ast
import hashlib

PREP=Path(__file__).resolve().parent
old=PREP/'launch_graph29_a0_control_profile01.py'
new=PREP/'launch_graph29_a0_pause5_profile01.py'
assert not new.exists()
source=old.read_bytes().decode('utf-8')
changes={
    'ROOT_GRAPH29_A0_CONTROL_REVIEW01':'ROOT_GRAPH29_A0_PAUSE5_REVIEW01',
    'ROOT_GRAPH29_A0_CONTROL_ACTUAL_FIT_REVIEW01':'ROOT_GRAPH29_A0_PAUSE5_ACTUAL_FIT_REVIEW01',
    'ROOT_GRAPH29_A0_CONTROL_DRY_REVIEW01':'ROOT_GRAPH29_A0_PAUSE5_DRY_REVIEW01',
    'prepare_graph29_a0_control_package01.py':'prepare_graph29_a0_pause5_package01.py',
    'e462f4d39e15a59918b894d7c92127818f9c458af4723fd33bccc0517955817b':'1ac1860a219519f466d54e55b084166e933b67a9958affcdd1fce38416d4e72c',
    'run_prepare_graph29_a0_control_package01.py':'run_prepare_graph29_a0_pause5_package01.py',
    'c1c71628907e61bebf6a016498ab8bbdf2ed34ab42d1065044916a0ca10cbeec':'947a562d36486ea379f45058c891039d157d9a7dd5d1cfee4fa814a919524349',
    'check_graph29_a0_continuous01.py':'check_graph29_a0_pause5_01.py',
    '005b5bf8bb69071c8ed48f0e0fdcc1361d99962952419f1f715c133f3d849d96':'11e64f74fdc9da73a04aad44389b4db99ed4639ac877a79e12b2560957576a68',
    'run_graph29_a0_continuous01.py':'run_graph29_a0_pause5_01.py',
    '1ea86c4af457157e143b3dfb14edef12476c83f57c19e98456aaec95e310f9a4':'d18c3602ceb0083d08b448c8c11b89ad361825d64fc53c67a03a68a92f9da904',
    'graph29_a0_continuous01_request.ROOT.json':'graph29_a0_pause5_01_request.ROOT.json',
    "('graph29-a0-control-profile-' + args.mode + '01')":"('graph29-a0-pause5-profile-' + args.mode + '01')",
    'timeout = 630 if args.mode == \'fit\' else 65':'timeout = 200 if args.mode == \'fit\' else 65',
}
for before,after in sorted(changes.items(),key=lambda item:len(item[0]),reverse=True):
    assert before in source,before
    source=source.replace(before,after)
ast.parse(source,filename=str(new))
new.write_bytes(source.encode('utf-8'))
print('PAUSE5_PROFILE_AST_PASS',hashlib.sha256(new.read_bytes()).hexdigest())
