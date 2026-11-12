"""Chia inner roles Junyi theo Protocol21, giữ outer fold4 lịch sử."""
from dataclasses import dataclass, asdict
import hashlib
import json
from collections.abc import Iterable


@dataclass(frozen=True)
class JunyiResearchRoles:
    train_users: tuple[str, ...]
    selection_users: tuple[str, ...]
    calibration_users: tuple[str, ...]
    outer_validation_users: tuple[str, ...]
    outer_fold: int = 4
    seed: int = 42
    algorithm: str = 'akt-junyi-research-role-rank-v1'
    rounding: str = 'ceil_each_tenth_then_train_remainder'

    @property
    def identity(self) -> str:
        raw = json.dumps(asdict(self), sort_keys=True, separators=(',', ':')).encode('utf-8')
        return hashlib.sha256(raw).hexdigest()


def make_junyi_research_roles(assignments: Iterable[tuple[str | int, int, str]]) -> JunyiResearchRoles:
    """Nhận metadata (user_id, fold, partition), không nhận events/correctness."""
    seen = set()
    outer_train, outer_validation = [], []
    for user, fold, partition in assignments:
        if (type(user) not in (str, int) or type(fold) is not int or fold not in range(5)
                or type(partition) is not str or partition != 'development'):
            raise ValueError('Unique Development learner identities and frozen folds required')
        user = str(user)
        if not user or '\x00' in user or user in seen:
            raise ValueError('Unique Development learner identities and frozen folds required')
        seen.add(user)
        if fold == 4:
            outer_validation.append(user)
        else:
            outer_train.append(user)
    if len(outer_train) < 10 or not outer_validation:
        raise ValueError('At least ten outer-train learners and nonempty outer validation required')

    def rank(user):
        key = f'akt-junyi-research-role-rank-v1|42|4|{user}'.encode('utf-8')
        return hashlib.sha256(key).hexdigest(), user

    ranked = sorted(outer_train, key=rank)
    tenth = (len(ranked) + 9) // 10
    return JunyiResearchRoles(
        train_users=tuple(sorted(ranked[2*tenth:])),
        selection_users=tuple(sorted(ranked[:tenth])),
        calibration_users=tuple(sorted(ranked[tenth:2*tenth])),
        outer_validation_users=tuple(sorted(outer_validation)),
    )
