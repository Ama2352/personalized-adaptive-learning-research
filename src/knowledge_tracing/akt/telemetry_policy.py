"""Giới hạn bộ nhớ telemetry, giữ hành vi mặc định của trainer lịch sử."""
from collections import deque


def resource_sample_policy(budget):
    limit = budget.get('resource_sample_limit')
    include_progress = budget.get('progress_resource_samples', True)
    if type(include_progress) is not bool:
        raise ValueError('Explicit boolean progress sample policy required')
    if limit is None:
        return [], include_progress
    if type(limit) is not int or not 2 <= limit <= 4096:
        raise ValueError('Resource sample ring must contain2..4096 samples')
    return deque(maxlen=limit), include_progress
