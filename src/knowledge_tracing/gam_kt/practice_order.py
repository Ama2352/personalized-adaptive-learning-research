"""Descriptive first-exposure order, nhận train-only events và không dùng labels."""

from collections import Counter


def summarize_practice_order(events, edges, *, allowed_users, outer_fold, max_events=120):
    first = {}
    seen = set()
    counts = Counter()
    previous = {}
    for row in events:
        user = str(row['user_id'])
        key = (row['time_done'], row['source_row'])
        if (user not in allowed_users or row['partition'] != 'development'
                or row['fold'] not in range(5) or row['fold'] == outer_fold):
            raise ValueError('practice-order learner scope violation')
        if row['source_row'] in seen or key <= previous.get(user, (-1, -1)):
            raise ValueError('duplicate source row or invalid chronology')
        seen.add(row['source_row'])
        previous[user] = key
        counts[user] += 1
        if counts[user] > max_events:
            raise ValueError('practice-order prefix cap exceeded')
        first.setdefault(user, {}).setdefault(str(row['exercise']), key)
    if set(first) != set(allowed_users):
        raise ValueError('practice-order cohort is incomplete')
    if len(edges) != len(set(edges)) or any(a == b or not a or not b for a, b in edges):
        raise ValueError('invalid practice-order graph edges')
    results = []
    for parent, child in sorted(edges):
        together = [mapping for mapping in first.values() if parent in mapping and child in mapping]
        precedes = sum(mapping[parent] < mapping[child] for mapping in together)
        results.append({'parent': parent, 'child': child, 'coobserved_learners': len(together),
                        'parent_first_count': precedes, 'child_first_count': len(together)-precedes,
                        'parent_first_fraction': precedes/len(together) if together else None})
    return {'learners': len(first), 'events': sum(counts.values()), 'edges': results,
            'exercise_learner_support': dict(sorted(Counter(exercise for mapping in first.values()
                                                           for exercise in mapping).items())),
            'scope': 'First exposure in bounded observed prefix, no causal instructional interpretation'}
