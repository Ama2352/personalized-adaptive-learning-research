import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from knowledge_tracing.bkt_baseline.adapter import fit_skill, predict_skill, verify_runtime


class AdapterTests(unittest.TestCase):
    def test_installed_runtime_fits_a_standard_model(self):
        metadata = verify_runtime()
        self.assertEqual(metadata["pyBKT_version"], "1.4.3")
        train = pd.DataFrame(
            {
                "user_id": ["u1", "u1", "u1", "u2", "u2", "u2"],
                "skill_name": ["s"] * 6,
                "correct": [0, 1, 1, 0, 0, 1],
                "order_id": [1, 2, 3, 1, 2, 3],
            }
        )
        model = fit_skill(train, "s", num_fits=1, seed=17)
        self.assertIn("s", model.coef_)

    def test_prediction_is_one_step_ahead_and_row_aligned(self):
        train = pd.DataFrame(
            {
                "user_id": ["u1", "u1", "u1", "u2", "u2", "u2"],
                "skill_name": ["s"] * 6,
                "correct": [0, 1, 1, 0, 0, 1],
                "order_id": [1, 2, 3, 1, 2, 3],
            }
        )
        model = fit_skill(train, "s", num_fits=1, seed=7)
        model.fit_model["s"].update(
            {
                "prior": 0.2,
                "learns": np.array([0.1]),
                "guesses": np.array([0.2]),
                "slips": np.array([0.1]),
                "forgets": np.array([0.0]),
            }
        )
        base = pd.DataFrame(
            {
                "user_id": ["new", "new", "new"],
                "skill_name": ["s"] * 3,
                "correct": [0, 0, 1],
                "order_id": [1, 2, 3],
                "source_row": [101, 102, 103],
            }
        )
        changed = base.copy()
        changed.loc[1, "correct"] = 1
        p1 = predict_skill(model, base)
        p2 = predict_skill(model, changed)
        self.assertEqual(p1["source_row"].tolist(), [101, 102, 103])
        np.testing.assert_allclose(p1["prediction"].iloc[:2], p2["prediction"].iloc[:2])
        self.assertNotAlmostEqual(p1["prediction"].iloc[2], p2["prediction"].iloc[2])

    def test_fit_stops_on_non_finite_parameters(self):
        class InvalidModel:
            def __init__(self, **kwargs):
                pass

            def fit(self, **kwargs):
                self.fit_model = {"s": {}}

            @property
            def coef_(self):
                return {"s": {"prior": np.nan, "learns": np.array([0.1])}}

        train = pd.DataFrame({
            "user_id": ["u1"], "skill_name": ["s"], "correct": [1], "order_id": [1]
        })
        with patch("knowledge_tracing.bkt_baseline.adapter.Model", InvalidModel):
            with self.assertRaises(FloatingPointError):
                fit_skill(train, "s", num_fits=1, seed=17)

    def test_prediction_stops_on_non_finite_values(self):
        class InvalidModel:
            coef_ = {"s": {"prior": 0.5}}

            def predict(self, **kwargs):
                return pd.DataFrame({"source_row": [1], "correct_predictions": [np.inf]})

        frame = pd.DataFrame({
            "user_id": ["u1"], "skill_name": ["s"], "correct": [1],
            "order_id": [1], "source_row": [1]
        })
        with self.assertRaises(FloatingPointError):
            predict_skill(InvalidModel(), frame)


if __name__ == "__main__":
    unittest.main()
