"""Adapter ablation simulator Paper2, prototype chờ chốt protocol nghiên cứu."""

import numpy as np


def build_pathway_policy(reference, *, signal: bool, parent_adaptation: bool, local_adaptation: bool):
    """Giữ predict/update/selector nguồn, tách đúng ba pathways trong context.

    Reference phải do paper2_reference.load_reference tạo. Không dùng adapter này
    thay GAM Junyi. Chỉ chạy unit parity cho đến khi experiment protocol được chốt.
    """
    if any(type(value) is not bool for value in (signal, parent_adaptation, local_adaptation)):
        raise ValueError('pathway switches must be explicit booleans')
    original = reference['estimator']['GAMKTPolicy']

    class PathwayPolicy(original):
        def _context(self, cid):
            state = self.states[cid]
            summary = self._graph_summary(cid)
            q_task, r_neg, decay = self.q_task, self.r_neg, self.time_decay_rate
            if parent_adaptation:
                q_task += .025 * summary['uncertainty'] + .020 * summary['deficit']
                decay += .004 * summary['deficit']
            if local_adaptation:
                struggling = (state.attempts >= 5 and len(state.recent_outcomes) >= 5
                              and float(np.mean(state.recent_outcomes)) < .40)
                r_neg *= .90 if struggling else 1.0
                decay += .004 * state.times_forgotten
            return {'q_task': float(np.clip(q_task, .01, .18)), 'r_pos': self.r_pos,
                    'r_neg': float(np.clip(r_neg, .50, 2.00)),
                    'decay': float(np.clip(decay, .01, .10)),
                    'graph_signal': summary['signal'] if signal else 0.0}

    policy = PathwayPolicy(True)
    policy.name = f'Paper2-pathways-S{int(signal)}P{int(parent_adaptation)}L{int(local_adaptation)}'
    return policy
