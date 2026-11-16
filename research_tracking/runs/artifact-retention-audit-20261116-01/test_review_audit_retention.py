"""Kiểm việc kết thúc training không làm mất giá trị audit checkpoint."""
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location('review_audit_retention', Path(__file__).with_name('review_audit_retention.py'))
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)


def test_unique_intermediate_state_must_be_retained():
    assert review.disposition({'category': 'UNUSED_RESUME_FINISHED_RUN'}) == 'KEEP_UNIQUE_AUDIT_CHECKPOINT'


def test_identical_bytes_still_require_lineage():
    assert review.disposition({'category': 'UNUSED_VERIFIED_DUPLICATE'}) == 'CONDITIONAL_DEDUP_RETAIN_CONTENT_AND_LINEAGE'


def test_upload_parts_require_reconstruction_proof():
    assert review.disposition({'category': 'UNUSED_VERIFIED_TRANSFER_PART'}) == 'CONDITIONAL_RECONSTRUCTIBLE_TRANSFER'
