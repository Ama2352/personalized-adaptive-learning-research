"""Đối chiếu snapshot đã lưu: tiêu chí query, mastery và lựa chọn CID.

Không gọi model/simulator; bảng đồng xuất hiện mô tả, không causal mediation.
"""
from collections import Counter
from itertools import product


def _need(ok, message):
    if not ok:
        raise ValueError(message)


def _key(row):
    seed, profile, event = row['seed'], row['profile'], row['event_id']
    _need(type(seed) is int and type(profile) is str and profile and
          type(event) is str and event.isdecimal() and str(int(event)) == event,
          'Khóa snapshot không hợp lệ')
    return seed, profile, int(event)


def analyze(masteries, controllers, node_order):
    """Join một-một; giữ mọi zero cell và từng quỹ đạo, không thêm research N."""
    _need(type(node_order) in (tuple, list) and len(node_order) == len(set(node_order))
          and len(node_order) > 0 and all(type(x) is str for x in node_order), 'Node order')
    _need(type(masteries) is list and type(controllers) is list and masteries and controllers,
          'Hai tập snapshot phải không rỗng')
    left, right = {}, {}
    for rows, target in ((masteries, left), (controllers, right)):
        for row in rows:
            key = _key(row)
            _need(key not in target, 'Trùng khóa snapshot')
            target[key] = row
    _need(left.keys() == right.keys(), 'Thiếu hoặc thừa snapshot ở phép join')
    joined = []
    for key in sorted(left):
        m, c = left[key], right[key]
        for name in ('M_any', 'query_native_M_changed', 'query_raw_criterion_changed'):
            _need(type(m[name]) is bool, 'Mastery flag phải boolean')
        for name in ('M_changed', 'R_changed', 'C_changed', 'B_changed', 'CID_changed', 'full_preview_changed'):
            _need(type(c[name]) is bool, 'Controller flag phải boolean')
        index = m['query_index']
        _need(type(index) is int and 0 <= index < len(node_order)
              and node_order[index] == c['query']['concept'], 'Query concept không khớp node order')
        changed = m['M_changed_indices']
        _need(type(changed) is list and all(type(i) is int and 0 <= i < len(node_order) for i in changed)
              and len(changed) == len(set(changed)), 'M changed indices')
        _need(m['M_any'] == bool(changed) == c['M_changed'] and
              m['query_native_M_changed'] == (index in changed), 'Mastery flags mâu thuẫn')
        _need(all(type(c[arm]['selected_index']) is int and 0 <= c[arm]['selected_index'] < len(node_order)
                  for arm in ('full', 'empty')), 'Selected CID index')
        _need(c['CID_changed'] == (c['full']['selected_index'] != c['empty']['selected_index']),
              'CID flag không khớp selected index')
        code = ''.join(str(int(x)) for x in
                       (m['query_native_M_changed'], m['query_raw_criterion_changed'], c['CID_changed']))
        joined.append(dict(seed=key[0], profile=key[1], event_id=str(key[2]),
                           query_concept=c['query']['concept'], code=code,
                           M_set_changed=m['M_any'], R_changed=c['R_changed'],
                           B_changed=c['B_changed']))
    groups = [('pooled', joined)]
    groups += [('profile:'+p, [r for r in joined if r['profile'] == p]) for p in sorted({r['profile'] for r in joined})]
    groups += [('seed:'+str(s), [r for r in joined if r['seed'] == s]) for s in sorted({r['seed'] for r in joined})]
    groups += [(f'trajectory:{s}:{p}', [r for r in joined if (r['seed'], r['profile']) == (s, p)])
               for s, p in sorted({(r['seed'], r['profile']) for r in joined})]
    cells = [''.join(bits) for bits in product('01', repeat=3)]
    output = {}
    for name, rows in groups:
        counts = Counter(r['code'] for r in rows)
        table = {code: counts[code] for code in cells}
        _need(sum(table.values()) == len(rows), 'Bảo toàn mẫu bảng')
        output[name] = dict(paired_snapshots=len(rows), cells=table,
            query_M_changes=sum(r['code'][0] == '1' for r in rows),
            query_raw_criterion_changes=sum(r['code'][1] == '1' for r in rows),
            CID_changes=sum(r['code'][2] == '1' for r in rows),
            first_witness_by_cell={code: next((r for r in rows if r['code'] == code), None) for code in cells})
    return dict(kind='CACHED_SNAPSHOT_COOCCURRENCE_NOT_CAUSAL_MEDIATION',
                code_order=['query_native_M_changed', 'query_raw_criterion_changed', 'CID_changed'],
                groups=output, new_independent_N=0, model_calls=0,
                scope_vi='Cùng snapshot full/empty; khác biệt phân loại, không temporal crossings, không calibration truth hoặc served learning outcomes.')
