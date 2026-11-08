"""Tách inner train/validation theo learner trong Development."""

from dataclasses import dataclass
import hashlib
import json
import math

import pandas as pd


@dataclass(frozen=True)
class InnerSplit:
    inner_train_users: tuple[str, ...]
    inner_val_users: tuple[str, ...]
    outer_fold: int
    split_hash: str


def make_inner_split(development_assignments: pd.DataFrame, *, outer_fold: int, seed: int = 42) -> InnerSplit:
    frame = development_assignments
    if not {'user_id', 'fold'} <= set(frame.columns) or outer_fold not in range(5):
        raise ValueError('invalid development assignments or outer fold')
    if 'partition' in frame and not frame.partition.eq('development').all():
        raise ValueError('only development assignments are allowed')
    if frame.user_id.isna().any() or frame.user_id.astype(str).duplicated().any() or not frame.fold.isin(range(5)).all():
        raise ValueError('invalid development learner assignments')
    users = [str(user) for user in frame.loc[frame.fold != outer_fold, 'user_id']]
    if len(users) < 2:
        raise ValueError('at least two outer-train learners are required')
    def rank(user: str) -> tuple[str, str]:
        return hashlib.sha256(f'akt-inner-v1|{seed}|{outer_fold}|{user}'.encode('utf-8')).hexdigest(), user
    ranked = sorted(users, key=rank)
    count = math.ceil(len(ranked) * 0.1)
    val, train = tuple(sorted(ranked[:count])), tuple(sorted(ranked[count:]))
    payload = json.dumps({'seed': seed, 'outer_fold': outer_fold, 'train': train, 'val': val},
                         sort_keys=True, separators=(',', ':')).encode('utf-8')
    return InnerSplit(train, val, outer_fold, hashlib.sha256(payload).hexdigest())
