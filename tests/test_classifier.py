"""Unit tests for src.classifier.Classifier.

Focus: the probability matrix handed to the Masker must be shaped
(n_samples, n_classes) with columns in the same order as ``classes_``.
"""
import unittest
from unittest.mock import MagicMock, patch

import numpy as np
from sklearn.linear_model import LogisticRegression

from src.classifier.Classifier import Classifier


def _mock_base_estimator(classes, proba):
    """A stand-in estimator that records fit() calls and returns fixed probabilities."""
    base = MagicMock(name="base_estimator")
    base.classes_ = np.asarray(classes)
    base.predict_proba.return_value = np.asarray(proba)
    return base


class TestClassifierFit(unittest.TestCase):
    def test_fit_clones_base_estimator_and_leaves_original_untouched(self):
        base = _mock_base_estimator(["A", "B"], [[0.5, 0.5]])
        cloned = _mock_base_estimator(["A", "B"], [[0.5, 0.5]])

        with patch("sklearn.base.clone", return_value=cloned) as mock_clone:
            clf = Classifier(base_estimator=base).fit("X", "y")

        mock_clone.assert_called_once_with(base)
        cloned.fit.assert_called_once_with("X", "y")
        base.fit.assert_not_called()
        self.assertIs(clf.base_estimator_, cloned)
        self.assertIs(clf.base_estimator, base)  # sklearn convention: params are not mutated

    def test_fit_forwards_fit_params(self):
        cloned = _mock_base_estimator(["A"], [[1.0]])
        with patch("sklearn.base.clone", return_value=cloned):
            Classifier(base_estimator=MagicMock()).fit("X", "y", sample_weight=[1, 2])
        cloned.fit.assert_called_once_with("X", "y", sample_weight=[1, 2])

    def test_fit_exposes_classes_from_fitted_estimator(self):
        cloned = _mock_base_estimator(["B", "A", "C"], [[0.2, 0.3, 0.5]])
        with patch("sklearn.base.clone", return_value=cloned):
            clf = Classifier(base_estimator=MagicMock()).fit("X", "y")
        np.testing.assert_array_equal(clf.classes_, ["B", "A", "C"])

    def test_default_estimator_is_logistic_regression(self):
        X = np.array([[0.0], [1.0], [0.1], [0.9]])
        y = np.array(["neg", "pos", "neg", "pos"])
        clf = Classifier().fit(X, y)
        self.assertIsInstance(clf.base_estimator_, LogisticRegression)
        np.testing.assert_array_equal(clf.classes_, ["neg", "pos"])


class TestClassifierOutputAlignment(unittest.TestCase):
    def setUp(self):
        self.proba = np.array([[0.1, 0.9], [0.8, 0.2], [0.5, 0.5]])
        self.base = _mock_base_estimator(["A", "B"], self.proba)
        with patch("sklearn.base.clone", return_value=self.base):
            self.clf = Classifier(base_estimator=MagicMock()).fit("X", "y")

    def test_transform_returns_base_predict_proba(self):
        out = self.clf.transform("X_new")
        self.base.predict_proba.assert_called_once_with("X_new")
        np.testing.assert_array_equal(out, self.proba)

    def test_transform_shape_is_n_samples_by_n_classes(self):
        out = self.clf.transform("X_new")
        self.assertEqual(out.shape, (3, len(self.clf.classes_)))

    def test_predict_proba_is_alias_for_transform(self):
        np.testing.assert_array_equal(self.clf.predict_proba("X_new"), self.clf.transform("X_new"))

    def test_probability_columns_follow_classes_order_end_to_end(self):
        """With a real estimator, argmax over transform() must recover the true label
        via classes_[argmax] -- this is exactly what Masker.predict relies on."""
        X = np.array([[0.0], [1.0], [0.05], [0.95], [0.02], [0.98]])
        y = np.array(["zebra", "apple", "zebra", "apple", "zebra", "apple"])
        clf = Classifier(base_estimator=LogisticRegression()).fit(X, y)
        probs = clf.transform(X)
        recovered = clf.classes_[np.argmax(probs, axis=1)]
        np.testing.assert_array_equal(recovered, y)
        # sklearn sorts classes lexically, regardless of first appearance in y
        np.testing.assert_array_equal(clf.classes_, ["apple", "zebra"])


if __name__ == "__main__":
    unittest.main()
