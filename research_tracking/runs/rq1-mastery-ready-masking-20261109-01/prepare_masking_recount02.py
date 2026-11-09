"""Giữ verifier01 và tạo bản02 đo riêng các điều kiện có thể trùng nhau."""
import hashlib
import json
from pathlib import Path

PREP = Path(__file__).resolve().parent
source = PREP / 'verify_masking_from_native_snapshots01.py'
raw = source.read_bytes()
snapshot = PREP / 'masking-independent-recount-before02'
snapshot.mkdir(exist_ok=False)
inventory = dict(source=source.name, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
with (snapshot / 'inventory-before.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(inventory, stream, indent=2)
    stream.write('\n')
with (snapshot / source.name).open('xb') as stream:
    stream.write(raw)
assert hashlib.sha256((snapshot / source.name).read_bytes()).hexdigest() == inventory['sha256']
failure = dict(kind='ROOT_INDEPENDENT_VERIFIER_EXPECTATION_FAILURE',
    observed_error='AssertionError at line136, expected mutually exclusive reason counts18/8/4',
    observed_from='Root tool output, no separate raw subprocess log was captured',
    source_sha256=inventory['sha256'], scientific_analyzer_changed=False,
    cached_analyzer_verdict='ACCEPTED',
    consequence_vi='Đo riêng child mastery và exposure để tránh gọi các điều kiện trùng nhau là nguyên nhân loại trừ.')
with (snapshot / 'failure-note.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(failure, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
text = raw.decode('utf-8')
old = """        if not children[node]:
            reason = 'no_direct_child_and_own_prerequisites_blocked'
            child = None
        else:
            assert len(children[node]) == 1
            child = children[node][0]
            if full[child] and empty[child]:
                reason = 'direct_child_already_mastered'
            else:
                assert history[node] >= 6
                reason = 'exposure_exception'
        event_reasons.append(dict(seed=key[0], profile=key[1], event_id=key[2],
                                 changed_concept=node, child=child, reason=reason))
"""
new = """        child = None if not children[node] else children[node][0]
        child_mastered = exposure = None
        if child is None:
            reason = 'no_direct_child_and_own_prerequisites_blocked'
        else:
            assert len(children[node]) == 1
            child_mastered = full[child] and empty[child]
            exposure = history[node] >= 6
            if child_mastered and exposure:
                reason = 'child_mastered_and_exposure'
            elif child_mastered:
                reason = 'child_mastered_without_exposure'
            elif exposure:
                reason = 'exposure_without_child_mastered'
            else:
                reason = 'other_parent_block'
        event_reasons.append(dict(seed=key[0], profile=key[1], event_id=key[2],
            changed_concept=node, child=child, child_mastered_both=child_mastered,
            exposure_exception=exposure, prior_visits=history[node], reason=reason))
"""
assert text.count(old) == 1
text = text.replace(old, new)
old = """assert reasons == dict(no_direct_child_and_own_prerequisites_blocked=18,
                       direct_child_already_mastered=8, exposure_exception=4)
"""
assert text.count(old) == 1
text = text.replace(old, "assert sum(reasons.values()) == 30\n")
text = text.replace("event_reason_counts=dict(reasons), event_reasons=event_reasons,", """event_reason_counts=dict(reasons), event_reasons=event_reasons,
    nonexclusive_predicate_counts=dict(
        child_mastered_both=sum(row['child_mastered_both'] is True for row in event_reasons),
        exposure_exception=sum(row['exposure_exception'] is True for row in event_reasons),
        both=sum(row['child_mastered_both'] is True and row['exposure_exception'] is True for row in event_reasons)),""")
text = text.replace("masking_independent_native_recount01.json", "masking_independent_native_recount02.json")
target = PREP / 'verify_masking_from_native_snapshots02.py'
with target.open('xb') as stream:
    stream.write(text.encode('utf-8'))
assert source.read_bytes() == raw
print(json.dumps(dict(status='PREPARED_RECOUNT02_PRESERVED01',
                     source01_sha256=inventory['sha256'], source02_sha256=hashlib.sha256(target.read_bytes()).hexdigest())))
