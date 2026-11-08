"""Twelve tiny stdlib fixtures; no actual cache/native/model imports or responses."""
from collections import Counter, deque
import gzip
import importlib.util
import inspect
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

SPEC = importlib.util.spec_from_file_location('mastery_trace_pure',Path(__file__).with_name('prediction_mastery_trace_worker01.py'))
a = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(a)  # Definitions only; main never called.


class FakePolicy:
    def __init__(self):
        self.states = {'A':SimpleNamespace(theta=1250.,pi_task=.55), 'B':SimpleNamespace(theta=1200.,pi_task=.2)}
        self.selection_counts = Counter(); self.question_counts = Counter(); self.recent_concepts = deque(maxlen=3)
        self.current_chapter = None
    def predict(self,cid,qid,difficulty,timestamp):
        return {'q1':.7,'q2':.5,'q3':.3}[qid]
    def is_mastered(self,cid):
        s = self.states[cid]; return s.theta >= 1250. and s.pi_task <= .55
    def mastery_score(self,cid): return .6 if cid == 'A' else .4
    def ready_set(self): return ['B']
    def select(self):
        self.selection_counts['B'] += 1
        return 'B','q3',1350.
    def update(self,cid,qid,difficulty,timestamp,y,p):
        self.states[cid].theta += y-p


def fingerprint(policy):
    return a.digest(dict(states={n:vars(v) for n,v in policy.states.items()},
        visits=dict(policy.selection_counts),questions=dict(policy.question_counts),
        recent=list(policy.recent_concepts),chapter=policy.current_chapter))


class TraceParityFixtures(unittest.TestCase):
    def query(self): return dict(concept='A',question='q2',difficulty=1200.)
    def refs(self): return [('q1',1050.),('q2',1200.),('q3',1350.)]
    def capture(self,policy=None):
        policy = policy or FakePolicy(); counts = Counter()
        def call(kind,fn,*args): counts[kind] += 1; return fn(*args)
        result = a.capture(policy,self.query(),['A','B'],self.refs(),None,call,fingerprint)
        return policy,counts,result
    def test_theta_and_uncertainty_inclusive_boundaries(self):
        self.assertEqual(a.predicates(1250.,.55),(True,True,True))
        self.assertEqual(a.predicates(1249.999,.55),(False,True,False))
        self.assertEqual(a.predicates(1250.,.550001),(True,False,False))
    def test_nonfinite_or_bool_theta_rejected(self):
        for theta in (True,float('nan'),float('inf')):
            with self.assertRaises(ValueError): a.predicates(theta,.3)
    def test_real_reference_identity_and_order_preserved(self):
        self.assertEqual(a.reference_items(self.refs(),'A',self.query()),self.refs())
    def test_reference_duplicate_or_wrong_difficulty_rejected(self):
        for refs in ([('q1',1050.),('q1',1200.),('q3',1350.)],[('q1',1000.),('q2',1200.),('q3',1350.)]):
            with self.assertRaises(ValueError): a.reference_items(refs,'A',self.query())
    def test_current_query_must_be_real_reference(self):
        with self.assertRaises(ValueError): a.reference_items(self.refs(),'B',self.query())
    def test_three_probs_use_one_current_and_two_frozen_probes(self):
        _,counts,(legacy,added) = self.capture()
        self.assertEqual(counts,dict(current_predict=1,reference_predict=2,preview_select=1,
            direct_ready_set=1,direct_mastery_score=2,direct_is_mastered=2))
        self.assertEqual([r['probability'] for r in added['raw_references']],[.7,.5,.3])
        self.assertEqual(legacy['probability'],added['raw_references'][1]['probability'])
    def test_capture_has_no_current_answer_and_keeps_original_state(self):
        self.assertNotIn('y',inspect.signature(a.capture).parameters)
        policy=FakePolicy(); before=fingerprint(policy)
        _,_,first=self.capture(policy); _,_,second=self.capture(policy)
        self.assertEqual(first,second); self.assertEqual(fingerprint(policy),before)
        self.assertEqual(policy.selection_counts,Counter())
    def test_reference_or_current_predict_mutation_rejects(self):
        class Mutating(FakePolicy):
            def predict(self,*args):
                self.states['A'].theta += 1
                return super().predict(*args)
        with self.assertRaisesRegex(ValueError,'state identity|mutated'): self.capture(Mutating())
    def test_native_M_can_differ_from_raw_reference_criterion(self):
        _,_,(legacy,added)=self.capture()
        self.assertEqual(legacy['mastered'],['A'])
        self.assertFalse(added['raw_reference_criterion'])  # raw .5 is not native mastery.
    def test_exact_admission_rejects_signed_zero_and_preview_mismatch(self):
        self.assertFalse(a.exact(0.,-0.))
        _,_,(legacy,added)=self.capture(); old=dict(legacy)
        a.admit(legacy,added['full_preview'],old,dict(preview=added['full_preview']))
        with self.assertRaises(ValueError): a.admit(legacy,added['full_preview'],old,dict(preview=dict(concept='A',question='q2',difficulty=1200.)))
    def test_observe_then_literal_logged_bookkeeping_only(self):
        p=FakePolicy();before=p.states['A'].theta;calls=[]
        def call(kind,fn,*args): calls.append(kind);return fn(*args)
        a.advance(p,self.query(),None,1,.5,{'A':'chapterA','B':'chapterB'},call)
        self.assertEqual(calls,['update']);self.assertEqual(p.states['A'].theta,before+.5)
        self.assertEqual(p.selection_counts,{'A':1});self.assertEqual(p.question_counts,{'q2':1})
        self.assertEqual(list(p.recent_concepts),['A']);self.assertEqual(p.current_chapter,'chapterA')
    def test_joint_partition_retains_all_zero_cells(self):
        left=[[1250.,.55,True,True,True],[1200.,.2,False,True,False]]
        right=[[1200.,.55,False,True,False],[1250.,.6,True,False,False]]
        counts=a.joint_cells(left,right)
        self.assertEqual(list(counts),[f'{i:03b}' for i in range(8)])
        self.assertEqual(sum(counts.values()),2);self.assertEqual(counts['101'],1);self.assertEqual(counts['110'],1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
