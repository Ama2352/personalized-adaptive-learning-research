"""Replay estimator CPU09 trước khi đối chiếu queried-concept mastery của world.

Import module chỉ dùng stdlib. Main native sẽ do owned worker riêng gọi sau review.
Truth chỉ được diễn giải sau khi mọi stream đạt parity, không đi vào estimator.
"""

import hashlib
import json
import math
import struct


OBSERVABLE_FIELDS = frozenset(('step', 'concept', 'question', 'prediction', 'y'))
MASTERY_ELO = 1250.0
NATIVE_PI_THRESHOLD = .55


def need(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def identity(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def clock_hours(steps):
    """Đúng vòng lặp clock CPU09, index0 được hỏi sau mốc bắt đầu6giờ."""
    need(type(steps) is int and 1 <= steps <= 120, 'CPU09 bounded stream length')
    current = 0
    result = []
    for step in range(steps):
        current += 72 if step > 0 and step % 28 == 0 else 6
        result.append(current)
    return tuple(result)


def observable_histories(buckets, *, seeds, profiles, steps):
    expected = {(s, p, g, m) for s in seeds for p in profiles
                for g in (False, True) for m in (False, True)}
    need(set(buckets) == expected, 'complete declared stream grid')
    projected = {}
    for key, rows in buckets.items():
        need(len(rows) == steps and [row['step'] for row in rows] == list(range(steps)), 'ordered complete steps')
        history = []
        for row in rows:
            value = {name: row[name] for name in OBSERVABLE_FIELDS}
            need(type(value['concept']) is str and type(value['question']) is str
                 and type(value['step']) is int and type(value['y']) is int and value['y'] in (0, 1)
                 and type(value['prediction']) is float and math.isfinite(value['prediction'])
                 and 0 <= value['prediction'] <= 1, 'observable row types')
            history.append(value)
        projected[key] = tuple(history)
    return projected


def capture_native(policy, concept, timestamp):
    """Đọc stored pi và decayed pi riêng, giữ nguyên predicate M của nguồn."""
    state = policy.states[concept]
    theta, stored_task, stored_time = state.theta, state.pi_task, state.pi_time
    need(all(finite(x) for x in (theta, stored_task, stored_time))
         and 0 <= stored_task <= 1 and 0 <= stored_time <= 1, 'native state finite/range')
    decayed_task, decayed_time, _ = policy._decayed_pi(concept, timestamp)
    need(all(finite(x) and 0 <= x <= 1 for x in (decayed_task, decayed_time)), 'decayed uncertainty finite/range')
    mastered = policy.is_mastered(concept)
    need(type(mastered) is bool and mastered == (theta >= MASTERY_ELO and stored_task <= NATIVE_PI_THRESHOLD),
         'literal native stored-pi mastery predicate')
    return dict(theta_est=float(theta), pi_task_stored=float(stored_task), pi_time_stored=float(stored_time),
                pi_task_decayed=float(decayed_task), pi_time_decayed=float(decayed_time), native_M=mastered,
                theta_gate=theta >= MASTERY_ELO, stored_pi_gate=stored_task <= NATIVE_PI_THRESHOLD)


def matched_replay(histories, *, seeds, profiles, steps, questions, policy_factory, timestamp_factory,
                   guard=lambda: None):
    """Factory chỉ nhận graph_on. Select/predict/update giữ thứ tự native CPU09."""
    keys = [(s, p, g, m) for s in seeds for p in profiles
            for g in (False, True) for m in (False, True)]
    need(set(histories) == set(keys), 'full replay grid')
    offsets = clock_hours(steps)
    result = []
    calls = dict(estimator_constructors=0, select=0, predict=0, native_capture=0, update=0)
    for seed, profile, graph_on, mechanism_on in keys:
        guard()
        policy = policy_factory(graph_on=graph_on)
        calls['estimator_constructors'] += 1
        history = histories[(seed, profile, graph_on, mechanism_on)]
        need(len(history) == steps, 'complete observable stream')
        for step, row in enumerate(history):
            guard()
            need(set(row) == OBSERVABLE_FIELDS and row['step'] == step, 'observable-only replay input')
            timestamp = timestamp_factory(offsets[step])
            selected = policy.select()
            calls['select'] += 1
            expected = questions[row['question']]
            need(type(selected) is tuple and len(selected) == 3
                 and selected[0] == row['concept'] == expected['concept']
                 and selected[1] == row['question'] and type(selected[2]) is float
                 and struct.pack('>d', selected[2]) == struct.pack('>d', expected['difficulty']),
                 'exact original selected query/difficulty parity')
            predicted = policy.predict(selected[0], selected[1], selected[2], timestamp)
            calls['predict'] += 1
            need(type(predicted) is float and math.isfinite(predicted) and 0 <= predicted <= 1
                 and struct.pack('>d', predicted) == struct.pack('>d', row['prediction']),
                 'exact archived probability bits parity')
            native = capture_native(policy, row['concept'], timestamp)
            calls['native_capture'] += 1
            result.append(dict(seed=seed, profile=profile, graph_on=graph_on, mechanism_on=mechanism_on,
                  step=step, concept=row['concept'], question=row['question'], difficulty=selected[2],
                  timestamp=timestamp.isoformat(), source_clock_hours=offsets[step], prediction=predicted, **native))
            # Y chỉ được truyền vào native tại bước update sau capture/parity.
            policy.update(selected[0], selected[1], selected[2], timestamp, row['y'], predicted)
            calls['update'] += 1
            guard()
        need(sum(state.attempts for state in policy.states.values()) == steps, 'all native updates complete')
    expected_events = len(keys) * steps
    need(len(result) == expected_events and calls == dict(estimator_constructors=len(keys), select=expected_events,
         predict=expected_events, native_capture=expected_events, update=expected_events), 'complete native direct-call ledger')
    parity = dict(status='ALL_STREAMS_EXACT_P_QUERY_SOURCE_CLOCK_PARITY_BEFORE_TRUTH', streams=len(keys),
                  events=expected_events, calls=calls, pretruth_readout_sha256=identity(result),
                  clock_origin='SOURCE_DERIVED_NOT_A_LOGGED_TIMESTAMP_FIELD', clock_hours=list(offsets))
    return result, parity


def confusion(rows):
    """Counts trên queried concepts, không thêm estimator hoặc response mới."""
    result = dict(rows=len(rows), truth_mastered=0, native_M_true=0, theta_gate_true=0,
                  stored_pi_gate_pass=0, theta_gate_true_pi_blocked=0, oracle_true_pi_blocked=0,
                  M_TP=0, M_FP=0, M_FN=0, M_TN=0, theta_TP=0, theta_FP=0, theta_FN=0, theta_TN=0)
    for row in rows:
        truth, mastered, theta, pi = (row[name] for name in ('source_true_M', 'native_M', 'theta_gate', 'stored_pi_gate'))
        need(all(type(value) is bool for value in (truth, mastered, theta, pi)) and mastered == (theta and pi),
             'evaluated boolean gates')
        result['truth_mastered'] += truth
        result['native_M_true'] += mastered
        result['theta_gate_true'] += theta
        result['stored_pi_gate_pass'] += pi
        result['theta_gate_true_pi_blocked'] += theta and not pi
        result['oracle_true_pi_blocked'] += truth and theta and not pi
        for label, predicted in (('M', mastered), ('theta', theta)):
            cell = 'TP' if predicted and truth else 'FP' if predicted else 'FN' if truth else 'TN'
            result[label + '_' + cell] += 1
    return result


def attach_truth_and_group(readouts, buckets, *, seeds, profiles, steps):
    """Chỉ orchestration sau full parity mới gọi hàm diễn giải truth này."""
    expected = {(s, p, g, m, t) for s in seeds for p in profiles
                for g in (False, True) for m in (False, True) for t in range(steps)}
    keys = [(r['seed'], r['profile'], r['graph_on'], r['mechanism_on'], r['step']) for r in readouts]
    need(len(keys) == len(expected) and set(keys) == expected, 'complete readout identity before truth join')
    evaluated = []
    for row, key in zip(readouts, keys):
        truth = buckets[key[:4]][key[4]]
        need((truth['step'], truth['concept'], truth['question']) == (row['step'], row['concept'], row['question'])
             and finite(truth['theta_before']), 'source truth/query identity')
        evaluated.append(dict(**row, source_true_theta_before=truth['theta_before'],
                              source_true_M=truth['theta_before'] >= MASTERY_ELO))
    grouped = {}
    for row in evaluated:
        key = (row['seed'], row['profile'], row['graph_on'], row['mechanism_on'])
        grouped.setdefault(key, []).append(row)
    result = []
    for seed in seeds:
        for profile in profiles:
            for g in (False, True):
                for m in (False, True):
                    result.append(dict(level='world', seed=seed, profile=profile, graph_on=g, mechanism_on=m,
                                       **confusion(grouped[(seed, profile, g, m)])))
    for profile in profiles:
        for g in (False, True):
            for m in (False, True):
                result.append(dict(level='persona_arm', seed=None, profile=profile, graph_on=g, mechanism_on=m,
                    **confusion([r for s in seeds for r in grouped[(s, profile, g, m)]])))
    for g in (False, True):
        for m in (False, True):
            result.append(dict(level='arm', seed=None, profile=None, graph_on=g, mechanism_on=m,
                **confusion([r for s in seeds for p in profiles for r in grouped[(s, p, g, m)]])))
    return evaluated, result


def replay_then_evaluate(buckets, *, seeds, profiles, steps, questions, policy_factory, timestamp_factory,
                         guard=lambda: None, verify_after=lambda: None):
    observable = observable_histories(buckets, seeds=seeds, profiles=profiles, steps=steps)
    readouts, parity = matched_replay(observable, seeds=seeds, profiles=profiles, steps=steps, questions=questions,
        policy_factory=policy_factory, timestamp_factory=timestamp_factory, guard=guard)
    verify_after()
    guard()
    evaluated, groups = attach_truth_and_group(readouts, buckets, seeds=seeds, profiles=profiles, steps=steps)
    guard()
    return dict(parity=parity, evaluated=evaluated, groups=groups)
