"""Regression tests for C++ E-step likelihood conversion to Python."""

import math
import unittest

import numpy as np

from pyBKT.fit import E_step


class TestEStepLikelihoodBinding(unittest.TestCase):
    def _likelihood(self, guess):
        prior = 0.4
        slip = 0.2
        data = {
            "data": np.array([[2]], dtype=np.int32),
            "resources": np.array([1], dtype=np.int64),
            "starts": np.array([1], dtype=np.int64),
            "lengths": np.array([1], dtype=np.int64),
        }
        model = {
            "prior": prior,
            "learns": np.array([0.2]),
            "forgets": np.array([0.0]),
            "guesses": np.array([guess]),
            "slips": np.array([slip]),
        }
        result = E_step.run(data, model, 1, 0, {})
        expected = math.log((1 - prior) * guess + prior * (1 - slip))
        self.assertIs(type(result["total_loglike"]), float)
        self.assertNotEqual(result["total_loglike"], round(result["total_loglike"]))
        self.assertAlmostEqual(result["total_loglike"], expected, places=14)
        return result["total_loglike"]

    def test_negative_fractional_log_likelihood_survives_binding(self):
        self.assertLess(self._likelihood(0.3), 0.0)

    def test_positive_fractional_log_likelihood_survives_binding(self):
        # An out-of-range emission probability isolates the C API conversion;
        # it is not a valid BKT model and is not used for fitting.
        self.assertGreater(self._likelihood(1.4), 0.0)


if __name__ == "__main__":
    unittest.main()
