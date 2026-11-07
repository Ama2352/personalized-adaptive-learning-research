"""Descriptive first-exposure order, nhận train-only events và không dùng labels."""

from collections import Counter


def _first_exposures(events, *, allowed_users, outer_fold, max_events):
    if not allowed_users or outer_fold not in range(5) or type(max_events) is not int or max_events < 1:
        raise ValueError('invalid practice-order scope or cap')
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
    return first, counts


def _validate_edges(edges):
    if len(edges) != len(set(edges)) or any(a == b or not a or not b for a, b in edges):
        raise ValueError('invalid practice-order graph edges')


def summarize_practice_order(events, edges, *, allowed_users, outer_fold, max_events=120):
    first, counts = _first_exposures(events, allowed_users=allowed_users, outer_fold=outer_fold,
                                     max_events=max_events)
    _validate_edges(edges)
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


def compare_order_controls(events, base_edges, control_edges, *, allowed_users, outer_fold, max_events=120):
    """Contrasts mô tả theo learner trên cùng (learner, observed child) opportunities.

    Denominator là số incoming edges cố định cho mỗi child, không chỉ edges
    co-observed. Missing parent và timestamp ties là categories riêng. Không
    suy missing = prerequisite fail hoặc dùng observed order làm learning gain.
    """
    first, counts = _first_exposures(events, allowed_users=allowed_users, outer_fold=outer_fold,
                                     max_events=max_events)
    _validate_edges(base_edges)
    _validate_edges(control_edges)
    if (Counter(b for a, b in base_edges) != Counter(b for a, b in control_edges)
            or Counter(a for a, b in base_edges) != Counter(a for a, b in control_edges)):
        raise ValueError('order controls require matched in/out degree')
    incoming = []
    for edges in (base_edges, control_edges):
        parents = {}
        for a, b in edges:
            parents.setdefault(b, set()).add(a)
        incoming.append(parents)
    metrics = ('observed_prior_fraction', 'observed_later_fraction', 'timestamp_tie_fraction',
               'unobserved_parent_fraction')
    paired = []
    common = []
    opportunities = common_opportunities = changed_opportunities = 0

    def rates(mapping, child, parents):
        counter = Counter()
        for parent in parents:
            if parent not in mapping:
                category = 'unobserved_parent_fraction'
            elif mapping[parent][0] < mapping[child][0]:
                category = 'observed_prior_fraction'
            elif mapping[parent][0] > mapping[child][0]:
                category = 'observed_later_fraction'
            else:
                category = 'timestamp_tie_fraction'
            counter[category] += 1
        return {key: counter[key] / len(parents) for key in metrics}

    def learner_mean(rows):
        return {key: sum(row[key] for row in rows) / len(rows) for key in metrics}

    for user in sorted(first):
        mapping = first[user]
        children = sorted(set(mapping) & set(incoming[0]))
        if not children:
            continue
        by_graph = [[], []]
        coobserved_by_graph = [[], []]
        for child in children:
            opportunities += 1
            changed_opportunities += incoming[0][child] != incoming[1][child]
            is_common = all(set(mapping) & parents[child] for parents in incoming)
            common_opportunities += int(is_common)
            for index, parents in enumerate(incoming):
                result = rates(mapping, child, parents[child])
                by_graph[index].append(result)
                if is_common:
                    coobserved_by_graph[index].append(result)
        paired.append([learner_mean(values) for values in by_graph])
        if coobserved_by_graph[0]:
            common.append([learner_mean(values) for values in coobserved_by_graph])

    def aggregate(rows):
        if not rows:
            return None
        base = learner_mean([row[0] for row in rows])
        control = learner_mean([row[1] for row in rows])
        changes = {}
        for key in metrics:
            differences = [row[1][key] - row[0][key] for row in rows]
            changes[key] = {'mean': sum(differences) / len(differences),
                'min': min(differences), 'max': max(differences),
                'positive_learners': sum(value > 1e-15 for value in differences),
                'negative_learners': sum(value < -1e-15 for value in differences),
                'unchanged_learners': sum(abs(value) <= 1e-15 for value in differences)}
        return {'learners': len(rows), 'base': base, 'control': control,
                'paired_control_minus_base': changes}

    return {'cohort_learners': len(first), 'events': sum(counts.values()),
        'eligible_learners': len(paired), 'excluded_no_incoming_child': len(first) - len(paired),
        'fixed_child_opportunities': opportunities, 'changed_parent_child_opportunities': changed_opportunities,
        'common_coobserved_child_opportunities': common_opportunities,
        'common_opportunity_retained_fraction': common_opportunities / opportunities if opportunities else None,
        'all_fixed_opportunities': aggregate(paired), 'common_coobserved_opportunities': aggregate(common),
        'inference_unit': 'learner; child averages within learner, equal weights across eligible learners',
        'denominator': 'all incoming edges per child, matched in-degree; missing parents retained separately',
        'scope': 'descriptive logged-prefix alignment only; no correctness, prediction or causal benefit claim'}
