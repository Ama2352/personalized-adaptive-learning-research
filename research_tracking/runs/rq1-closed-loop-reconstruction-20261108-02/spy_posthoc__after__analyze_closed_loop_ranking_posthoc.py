"""Explicit post-hoc native concept-key replay from already-called B scores."""
import argparse
from collections import Counter
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path
import time

from analyze_closed_loop_descriptive import tuple_key, timestamp_key

PREP = Path(__file__).resolve().parent
ROOT = PREP.parents[3]
VARIANTS = ('graph_free', 'graph_package', 'empty_graph_package')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replay_key(row, visits, previous_chapter, chapters):
    balanced = row['balanced_candidates']
    calls = row['mastery_score_calls']
    if (not balanced or len(balanced) != len(set(balanced)) or len(calls) != len(balanced)
            or [v['concept'] for v in calls] != balanced):
        raise ValueError('captured native scores do not uniquely/order-exactly cover B')
    scores = {value['concept']: value['score'] for value in calls}
    if any(type(value) is not float or not math.isfinite(value) for value in scores.values()):
        raise ValueError('nonfinite/non-binary64 native score')
    keys = {cid: (scores[cid], 0 if chapters[cid] == previous_chapter else 1, visits[cid], cid)
            for cid in balanced}
    chosen = min(balanced, key=keys.__getitem__)
    if chosen != row['served_tuple']['concept']:
        raise ValueError('native concept min does not match served concept; no explanation claim')
    return {'chosen_concept': chosen, 'B': list(balanced),
            'native_keys': {cid: {'score': key[0], 'score_hex': key[0].hex(),
                'chapter_tie': key[1], 'prior_visits': key[2], 'lexical_cid': key[3]} for cid, key in keys.items()},
            'previous_chapter': previous_chapter,
            'all_prior_visits': {cid: visits[cid] for cid in sorted(row['mastered_decisions'])}}


def analyze(rows, chapters, *, seeds, profiles, steps, check=lambda: None):
    indexed = {(v['seed'], v['profile'], v['variant'], v['step']): v for v in rows}
    expected = {(s, p, v, t) for s in seeds for p in profiles for v in VARIANTS for t in range(steps)}
    if len(indexed) != len(rows) or set(indexed) != expected:
        raise ValueError('all trajectories/events required')
    replays, unsupported = {}, []
    for seed in seeds:
        for profile in profiles:
            for variant in VARIANTS:
                visits, previous = Counter(), None
                for step in range(steps):
                    check()
                    key = seed, profile, variant, step
                    row = indexed[key]
                    if sum(visits.values()) != step or not set(row['mastered_decisions']) <= chapters.keys():
                        raise ValueError('prior-count/chapter boundary invalid')
                    try:
                        replays[key] = replay_key(row, visits, previous, chapters)
                    except (ValueError, KeyError) as exc:
                        unsupported.append({'key': list(key), 'reason': str(exc)})
                    chosen = row['served_tuple']['concept']
                    visits[chosen] += 1
                    previous = chapters[chosen]
    comparisons = []
    for seed in seeds:
        for profile in profiles:
            for candidate in VARIANTS[1:]:
                first_break, all_common_contexts_equal, common = None, True, True
                common_before = 0
                for step in range(steps):
                    leftkey, rightkey = (seed, profile, 'graph_free', step), (seed, profile, candidate, step)
                    left, right = indexed[leftkey], indexed[rightkey]
                    if not common:
                        continue
                    common_before += 1
                    lrank, rrank = replays.get(leftkey), replays.get(rightkey)
                    same_tie_context = bool(lrank and rrank and lrank['all_prior_visits'] == rrank['all_prior_visits']
                                            and lrank['previous_chapter'] == rrank['previous_chapter'])
                    all_common_contexts_equal = all_common_contexts_equal and same_tie_context
                    same_tuple = tuple_key(left) == tuple_key(right)
                    same_time = timestamp_key(left) == timestamp_key(right)
                    same_label = left['correct'] == right['correct']
                    common = same_tuple and same_time and same_label
                    if common:
                        continue
                    reasons = [name for name, same in [('served_tuple', same_tuple), ('timestamp', same_time), ('label', same_label)] if not same]
                    first_break = {'step': step, 'reasons': reasons, 'common_before': True,
                                   'tie_context_equal': same_tie_context}
                    if same_tuple:
                        first_break['classification'] = 'PREFIX_BREAK_WITHOUT_CURRENT_TUPLE_DIFF_NO_RANK_BREAK_CLAIM'
                    elif lrank is None or rrank is None or not same_tie_context:
                        first_break['classification'] = 'UNSUPPORTED_CAPTURE_OR_TIE_CONTEXT_NO_FILL'
                    else:
                        same_sets = {name: set(left[field]) == set(right[field]) for name, field in
                            [('R', 'ready_set'), ('C', 'eligible_candidates'), ('B', 'balanced_candidates')]}
                        same_sets['M'] = ({cid for cid, value in left['mastered_decisions'].items() if value}
                                          == {cid for cid, value in right['mastered_decisions'].items() if value})
                        different_concept = lrank['chosen_concept'] != rrank['chosen_concept']
                        first_break.update(same_membership_sets=same_sets, different_chosen_concept=different_concept,
                                           left_native_replay=lrank, right_native_replay=rrank)
                        if not different_concept:
                            classification = 'ITEM_ONLY_DIFF_NOT_EXPLAINED_BY_CONCEPT_RANK'
                        elif not same_sets['B']:
                            classification = 'B_MEMBERSHIP_DIFF_SCORE_ONLY_EXPLANATION_NOT_CLAIMED'
                        else:
                            same_non_score_keys = all(
                                {k: value for k, value in lrank['native_keys'][cid].items() if k not in ('score', 'score_hex')}
                                == {k: value for k, value in rrank['native_keys'][cid].items() if k not in ('score', 'score_hex')}
                                for cid in lrank['B'])
                            differing_scores = [cid for cid in sorted(lrank['B']) if
                                lrank['native_keys'][cid]['score_hex'] != rrank['native_keys'][cid]['score_hex']]
                            if not same_non_score_keys or not differing_scores:
                                classification = 'INCONSISTENT_SCORE_EXPLANATION_STOP_CLAIM'
                            else:
                                classification = 'SAME_B_TIES_NATIVE_B_SCORE_RANKING_EXPLAINS_CONCEPT_CHOICE'
                            first_break.update(same_non_score_keys=same_non_score_keys,
                                               B_concepts_with_different_captured_scores=differing_scores)
                        first_break['classification'] = classification
                supported_count = sum((seed, profile, variant, t) in replays for variant in ('graph_free', candidate)
                                      for t in range(steps))
                comparisons.append({'seed': seed, 'profile': profile, 'candidate': candidate,
                    'common_before_events': common_before, 'rank_replayed_events_both_sides_all_steps': supported_count,
                    'all_common_before_tie_contexts_equal': all_common_contexts_equal,
                    'first_prefix_break': first_break,
                    'negative_case': first_break is None})
    return {'status': 'POST_HOC_EXPLORATORY_SOURCE_LEVEL_CONCEPT_DECISION_EXPLANATION_PENDING_PARENT_REVIEW',
            'ranking_key': ['captured native mastery_score(cid)', 'chapter tie 0/1', 'all prior served concept visits', 'lexical cid'],
            'events': len(rows), 'rank_replays_validated': len(replays), 'unsupported': unsupported,
            'comparison_count': len(comparisons), 'comparisons': comparisons, 'new_independent_N': 0,
            'native_policy_model_rng_calls': 0, 'original_a585_whole_source_recovered': False,
            'limits_vi': ['Post-hoc exploration, không preregistered effect hoặc causal mediation/learning benefit/edge-only effect.',
                'Key replay giải thích chosen concept, không chạy lại choose_question hoặc giải thích toàn bộ item/difficulty rule.',
                'Bscore đã gọi đủ cho local concept ranking; fullS28 không cần cho lời giải thích local này, nhưng calibration/global mastery/reference probe vẫn thiếu.',
                'Native order select(Bscore key)→predict(served item P)→interact→update. Served-item P sau bookkeeping không là causal parent của same-step selection; P ảnh hưởng future state qua update.',
                'Empty chỉ estimator-empty; controller G và environment G chung. Same observed prefix không phải randomized scientific intervention.']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-inventory', type=Path, required=True)
    parser.add_argument('--source-inventory-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--remaining-seconds', type=float, required=True)
    args = parser.parse_args()
    start = time.perf_counter()
    if not math.isfinite(args.remaining_seconds) or not 0 < args.remaining_seconds <= 15:
        raise ValueError('posthoc bound15s')
    def check():
        if time.perf_counter() - start > args.remaining_seconds:
            raise TimeoutError('posthoc cumulative15s')
    inventory = json.loads(args.source_inventory.read_text())
    if args.source_inventory.resolve().parent != PREP or sha(args.source_inventory) != args.source_inventory_sha256:
        raise ValueError('posthoc source freeze mismatch')
    def verify():
        for rel, value in inventory['files_sha256'].items():
            if sha(ROOT / rel) != value:
                raise ValueError('posthoc source/input drift: ' + rel)
    verify()
    chapter_path = ROOT / inventory['chapter_map_path']
    with chapter_path.open(encoding='utf-8-sig', newline='') as stream:
        chapters = {r['concept_id']: r['chapter'] for r in csv.DictReader(stream)}
    if any(not value or value.isnumeric() for value in chapters.values()):
        raise ValueError('chapter parser dtype equivalence not established')
    rows = []
    with gzip.open(PREP / 'closed-loop-fast-model-attempt01/observed_metadata.jsonl.gz', 'rt', encoding='utf-8') as stream:
        for line in stream:
            check()
            if len(line) > 65536 or len(rows) >= 3240:
                raise ValueError('bounded rows')
            rows.append(json.loads(line))
    result = analyze(rows, chapters, seeds=(20000, 20001, 20002), profiles=('PG', 'PY', 'PYH'), steps=120, check=check)
    result['source_inventory_sha256'] = args.source_inventory_sha256
    result['source_facts'] = inventory['source_facts']
    verify();check()
    output = args.output.resolve()
    if output.parent != PREP or output.exists():
        raise ValueError('exclusive posthoc output required')
    output.mkdir(exist_ok=False)
    with (output / 'ranking_candidate.json').open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2);stream.write('\n')
    verify();check()
    receipt = {'status': 'PASS_READONLY_POSTHOC_CANDIDATE_PARENT_REVIEW_PENDING',
               'elapsed_seconds': time.perf_counter() - start, 'source_inventory_sha256': args.source_inventory_sha256,
               'candidate_sha256': sha(output / 'ranking_candidate.json'), 'native_model_rng_calls': 0,
               'exante_outputs_edited': False, 'report_section_appended': False}
    with (output / 'receipt.json').open('x', encoding='utf-8') as stream:
        json.dump(receipt, stream, ensure_ascii=False, indent=2);stream.write('\n')


if __name__ == '__main__':
    main()
