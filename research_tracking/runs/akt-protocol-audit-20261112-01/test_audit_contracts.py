"""Gài lỗi hữu hạn để kiểm audit bắt đúng config, epoch và target sai."""
import copy
import importlib.util
import math
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('akt_contract_audit', Path(__file__).with_name('audit_contracts.py'))
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class AuditContractTests(unittest.TestCase):
    def test_frozen_recipe_accepted(self):
        audit.check_recipe(copy.deepcopy(audit.FROZEN))

    def test_wrong_architecture_optimizer_and_seed_rejected(self):
        for name, value in [('batch_size',8),('d_model',32),('n_pid',1),('seed',43),('lr',0.001),('device','cpu')]:
            config=copy.deepcopy(audit.FROZEN);config[name]=value
            with self.subTest(field=name), self.assertRaisesRegex(ValueError,'recipe:'+name):
                audit.check_recipe(config)

    def history(self):
        return [dict(epoch=index,raw_selection=dict(native_bce_mean=loss),selected_epoch=best)
                for index,loss,best in [(1,.6,1),(2,.5,2),(3,.5002,2),(4,.5003,2),(5,.5004,2)]]

    def test_epoch_choice_and_patience_replayed(self):
        self.assertEqual(audit.replay_stopping(self.history(),audit.FROZEN),(2,[1,2]))

    def test_wrong_checkpoint_and_premature_stop_rejected(self):
        rows=self.history();rows[-1]['selected_epoch']=5
        with self.assertRaisesRegex(ValueError,'selected-state'):
            audit.replay_stopping(rows,audit.FROZEN)
        with self.assertRaisesRegex(ValueError,'premature'):
            audit.replay_stopping(self.history()[:-1],audit.FROZEN)

    def population(self):
        query=dict(item_id='item',timestamp=100,source_row=1)
        row=dict(learner_id='learner',global_rank='0',item_id='item',timestamp='100',source_row='1',
                 origin_role='selection',phase_scope='raw_selection10',history_used='0',
                 history_available='0',context_reset='False',support_reason='supported')
        truth=dict(row,correct='1')
        return [row],[truth],{('learner',0):(query,1)}

    def test_matched_population_accepted(self):
        audit.check_population(*self.population())

    def test_wrong_role_label_or_history_rejected(self):
        for name,value in [('origin_role','calibration'),('source_row','2'),('history_used','1')]:
            predictions,targets,expected=self.population();predictions[0][name]=value
            with self.subTest(field=name), self.assertRaises(ValueError):
                audit.check_population(predictions,targets,expected)
        predictions,targets,expected=self.population();targets[0]['correct']='0'
        with self.assertRaisesRegex(ValueError,'truth differs'):
            audit.check_population(predictions,targets,expected)

    def test_metrics_match_known_two_target_example(self):
        result=audit.recompute_metrics([dict(probability='0.2'),dict(probability='0.8')],
                                       [dict(correct='0'),dict(correct='1')])
        self.assertAlmostEqual(result['log_loss'],-math.log(.8))
        self.assertAlmostEqual(result['brier'],.04)
        self.assertAlmostEqual(result['ece'],.2)
        self.assertEqual(result['auc'],1.)


if __name__=='__main__':
    unittest.main()
