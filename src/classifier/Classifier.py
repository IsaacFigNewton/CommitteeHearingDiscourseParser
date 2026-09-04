from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin


class Classifier(BaseEstimator, TransformerMixin):
    """Transformer that wraps a classifier and outputs probabilities.

    This component wraps any sklearn-compatible classifier and transforms
    input features into probability distributions via predict_proba().
    It acts as a transformer in a pipeline, allowing the masking stage
    to be the final predictor.

    Typical usage in a Pipeline:
        Pipeline([
            ('features', feature_transformer),
            ('classifier', Classifier(base_estimator=LogisticRegression(max_iter=2000))),
            ('masker', Masker(parser=parser)),  # Final predictor
        ])
    """

    def __init__(self, base_estimator: Any = None) -> None:
        """Initialize the classifier wrapper.

        Args:
            base_estimator: Underlying classifier (e.g., LogisticRegression).
                           If None, LogisticRegression will be used as default.
        """
        self.base_estimator = base_estimator

    def fit(self, X: Any, y: Any, **fit_params: Any) -> "Classifier":
        """Fit the base classifier.

        Args:
            X: Training data
            y: Target labels
            **fit_params: Additional parameters for base estimator's fit

        Returns:
            self
        """
        from sklearn.linear_model import LogisticRegression
        from sklearn.base import clone

        if self.base_estimator is None:
            self.base_estimator_ = LogisticRegression()
        else:
            self.base_estimator_ = clone(self.base_estimator)

        self.base_estimator_.fit(X, y, **fit_params)
        self.classes_ = self.base_estimator_.classes_
        return self

    def transform(self, X: Any) -> np.ndarray:
        """Transform features into probability distributions.

        Args:
            X: Input data of shape (n_samples, n_features)

        Returns:
            Probability matrix of shape (n_samples, n_classes)
        """
        return self.base_estimator_.predict_proba(X)

    def predict_proba(self, X: Any) -> np.ndarray:
        """Return class probabilities (alias for transform).

        Args:
            X: Input data

        Returns:
            Probability matrix of shape (n_samples, n_classes)
        """
        return self.transform(X)
