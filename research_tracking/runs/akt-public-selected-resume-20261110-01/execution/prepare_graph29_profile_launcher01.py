"""Derive launcher process-private đã dùng trước, giữ originals nguyên byte."""
from pathlib import Path
import hashlib
import ast

PREP=Path(__file__).resolve().parent
original=PREP/'launch_tiny_a0_profile02.py'
target=PREP/'launch_graph29_a0_control_profile01.py'
assert not target.exists()
source=original.read_bytes().decode('utf-8')
changes={
    'ROOT_MAIN_TINY_A0_REVIEW01':'ROOT_GRAPH29_A0_CONTROL_REVIEW01',
    'prepare_main_tiny_a0_package01.py':'prepare_graph29_a0_control_package01.py',
    '05d30f2e5e408de7156b464ee0f7d566d049213ea3a8e54da2fbaed56a1f9249':'e462f4d39e15a59918b894d7c92127818f9c458af4723fd33bccc0517955817b',
    'run_prepare_main_tiny_a0_package01.py':'run_prepare_graph29_a0_control_package01.py',
    'caaf8ed2107860aa38167c6a05c3c3b88a78f89620c885a38d28a709198e2d0a':'c1c71628907e61bebf6a016498ab8bbdf2ed34ab42d1065044916a0ca10cbeec',
    'check_main_tiny_selected_a0_01.py':'check_graph29_a0_continuous01.py',
    '3720a51901f416b5cacbe2e144e3ed09598d3be8000944bd656c963853dac5e7':'005b5bf8bb69071c8ed48f0e0fdcc1361d99962952419f1f715c133f3d849d96',
    'run_main_tiny_selected_a0_02.py':'run_graph29_a0_continuous01.py',
    '3dac9e4efa6f8841de0f13565b618653a2bfdd3970b414341680579392a61cf7':'1ea86c4af457157e143b3dfb14edef12476c83f57c19e98456aaec95e310f9a4',
    'main_tiny_selected_a0_02_request.ROOT.json':'graph29_a0_continuous01_request.ROOT.json',
    'ROOT_MAIN_TINY_A0_ACTUAL_FIT_REVIEW02':'ROOT_GRAPH29_A0_CONTROL_ACTUAL_FIT_REVIEW01',
    'ROOT_MAIN_TINY_A0_DRY_REVIEW01':'ROOT_GRAPH29_A0_CONTROL_DRY_REVIEW01',
    "('tiny-a0-profile-' + args.mode + '02')":"('graph29-a0-control-profile-' + args.mode + '01')",
}
# Longest literal first avoids replacing metadata worker names within outer names.
for old,new in sorted(changes.items(),key=lambda item:len(item[0]),reverse=True):
    assert old in source,old
    source=source.replace(old,new)
old='assert not set(inherited) - set(expected) - display'
new='assert all(key in display or key in expected and value == expected[key] for key, value in inherited.items())'
assert source.count(old)==1
source=source.replace(old,new)
ast.parse(source,filename=str(target))
target.write_bytes(source.encode('utf-8'))
print('PROFILE_LAUNCHER_AST_PASS',hashlib.sha256(target.read_bytes()).hexdigest())
