"""Convergence and numerical failure guards for the C++ pyBKT backend."""

import unittest
from unittest.mock import patch

import numpy as np

from pyBKT.fit import EM_fit


def _e_step(loglike):
    return {
        "total_loglike": loglike,
        "all_trans_softcounts": np.zeros((1, 2, 2)),
        "all_emission_softcounts": np.zeros((1, 2, 2)),
        "all_initial_softcounts": np.zeros((2, 1)),
    }


class EMFitGuardTests(unittest.TestCase):
    def test_default_tolerance_matches_approved_python_configuration(self):
        values = iter([10.0, 9.0, 8.0, 7.996, 7.996])
        model = {"learns": np.array([0.1])}
        data = {"data": np.zeros((1, 1))}
        with patch.object(EM_fit.E_step, "run", side_effect=lambda *a, **k: _e_step(next(values))):
            with patch.object(EM_fit.M_step, "run", side_effect=lambda model, *a, **k: model):
                _, likelihoods = EM_fit.EM_fit(model, data, parallel=False)
        self.assertEqual(len(likelihoods), 4)

    def test_non_finite_likelihood_stops_fit(self):
        model = {"learns": np.array([0.1])}
        data = {"data": np.zeros((1, 1))}
        with patch.object(EM_fit.E_step, "run", return_value=_e_step(np.nan)):
            with patch.object(EM_fit.M_step, "run", side_effect=lambda model, *a, **k: model):
                with self.assertRaises(FloatingPointError):
                    EM_fit.EM_fit(model, data, parallel=False)


if __name__ == "__main__":
    unittest.main()
