from pathlib import Path
import tempfile
import unittest

import pandas as pd
from unittest.mock import patch

import knowledge_tracing.bkt_baseline.pipeline as pipeline
from knowledge_tracing.bkt_baseline.pipeline import run_pilot, run_cv, run_final_fit, run_test_once


class TinyStore:
    def __init__(self):
        self.test_reads = 0

    def development_support(self, pilot_fold=0):
        return pd.DataFrame([{"exercise": "s", "train_students": 4, "validation_students": 1, "train_rows": 12}])

    def load_development_skill(self, skill):
        assert skill in ("s", "t")
        rows = []
        outcomes = ([0, 1, 1], [1, 0, 1], [0, 0, 1], [1, 1, 0], [0, 1, 0])
        for user_index in range(5):
            for order in range(1, 4):
                rows.append(
                    {
                        "user_id": f"u{user_index}",
                        "exercise": skill,
                        "skill_name": skill,
                        "correct": outcomes[user_index][order - 1],
                        "suggested": user_index % 2,
                        "order_id": order,
                        "source_row": user_index * 3 + order,
                        "time_done": order,
                        "fold": user_index,
                    }
                )
        return pd.DataFrame(rows)

    def test_skills(self):
        return ["s", "unseen"]

    def load_test_skill(self, skill):
        self.test_reads += 1
        return pd.DataFrame(
            {
                "user_id": ["new", "new"],
                "exercise": [skill] * 2,
                "skill_name": [skill] * 2,
                "correct": [0, 1],
                "suggested": [0, 1],
                "order_id": [1, 2],
                "source_row": [100 if skill == "s" else 200, 101 if skill == "s" else 201],
                "time_done": [1, 2],
            }
        )


class PipelineTests(unittest.TestCase):
    def test_cv_resumes_completed_skill_folds_after_interruption(self):
        store = TinyStore()
        parent = Path("artifacts/bkt_baseline/test_tmp")
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as root:
            cv_dir = Path(root) / "cv"
            original = pipeline.fit_skill
            calls = 0

            def fail_after_two(*args, **kwargs):
                nonlocal calls
                calls += 1
                if calls == 3:
                    raise RuntimeError("simulated CV interruption")
                return original(*args, **kwargs)

            with patch.object(pipeline, "fit_skill", side_effect=fail_after_two):
                with self.assertRaisesRegex(RuntimeError, "simulated CV interruption"):
                    run_cv(store, cv_dir, skills=["s"], num_fits=1, seed=7)
            self.assertTrue((cv_dir / "cv_progress.json").is_file())
            result = run_cv(store, cv_dir, skills=["s"], num_fits=1, seed=7)
            self.assertEqual(len(result["folds"]), 5)
            self.assertEqual(len(result["fit_log"]), 5)

    def test_cv_resume_does_not_reload_fully_checkpointed_skills(self):
        store = TinyStore()
        store.loads = []
        original_load = store.load_development_skill

        def tracked_load(skill):
            store.loads.append(skill)
            return original_load(skill)

        store.load_development_skill = tracked_load
        parent = Path("artifacts/bkt_baseline/test_tmp")
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as root:
            cv_dir = Path(root) / "cv"
            original_fit = pipeline.fit_skill
            calls = 0

            def fail_during_second_skill(train, skill, *args, **kwargs):
                nonlocal calls
                calls += 1
                if calls == 6:
                    raise RuntimeError("simulated interruption")
                return original_fit(train, skill, *args, **kwargs)

            with patch.object(pipeline, "fit_skill", side_effect=fail_during_second_skill):
                with self.assertRaisesRegex(RuntimeError, "simulated interruption"):
                    run_cv(store, cv_dir, skills=["s", "t"], num_fits=1, seed=7)
            self.assertEqual(store.loads, ["s", "t"])
            store.loads.clear()
            result = run_cv(store, cv_dir, skills=["s", "t"], num_fits=1, seed=7)
            self.assertEqual(store.loads, ["t"])
            self.assertEqual(len(result["fit_log"]), 10)

    def test_pilot_resumes_completed_fits_after_interruption(self):
        store = TinyStore()
        parent = Path("artifacts/bkt_baseline/test_tmp")
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as root:
            pilot_dir = Path(root) / "pilot"
            original = pipeline.fit_skill
            calls = 0

            def fail_after_one(*args, **kwargs):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise RuntimeError("simulated interruption")
                return original(*args, **kwargs)

            with patch.object(pipeline, "fit_skill", side_effect=fail_after_one):
                with self.assertRaisesRegex(RuntimeError, "simulated interruption"):
                    run_pilot(store, pilot_dir, skills=["s"], num_fits=(1, 5), seeds=(7, 29))
            self.assertTrue((pilot_dir / "pilot_progress.json").is_file())
            result = run_pilot(store, pilot_dir, skills=["s"], num_fits=(1, 5), seeds=(7, 29))
            self.assertEqual(len(result["runs"]), 4)
            self.assertEqual(len(result["runs"][0]["skills"]), 1)

    def test_pilot_and_cv_use_only_development(self):
        store = TinyStore()
        parent = Path("artifacts/bkt_baseline/test_tmp")
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as root:
            pilot = run_pilot(store, Path(root) / "pilot", skills=["s"], num_fits=(1, 5), seeds=(7,))
            self.assertIn(pilot["selected_num_fits"], (1, 5))
            self.assertEqual(pilot["runs"][0]["skills"][0]["fit_seed"], pilot["runs"][1]["skills"][0]["fit_seed"])
            cv = run_cv(store, Path(root) / "cv", skills=["s"], num_fits=1, seed=7)
            self.assertEqual(len(cv["folds"]), 5)
            self.assertEqual(store.test_reads, 0)

    def test_holdout_is_guarded_and_unseen_has_no_prediction(self):
        store = TinyStore()
        parent = Path("artifacts/bkt_baseline/test_tmp")
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as root:
            root = Path(root)
            run_final_fit(store, root / "final", skills=["s"], num_fits=1, seed=7)
            result = run_test_once(store, root / "final", root / "test")
            self.assertEqual(result["overall"]["unseen_rows"], 2)
            self.assertEqual(result["overall"]["scored_rows"], 2)
            reads = store.test_reads
            with self.assertRaises(FileExistsError):
                run_test_once(store, root / "final", root / "test")
            self.assertEqual(store.test_reads, reads)


if __name__ == "__main__":
    unittest.main()
