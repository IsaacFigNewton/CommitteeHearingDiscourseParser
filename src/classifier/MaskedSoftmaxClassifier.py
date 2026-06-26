from __future__ import annotations

from typing import Any, Iterable, List, Optional, Sequence

import numpy as np
from sklearn.linear_model import LogisticRegression

from src.classifier.MaskedSoftmaxHelper import MaskedSoftmaxHelper

class MaskedSoftmaxClassifier(LogisticRegression):
    """LogisticRegression classifier with grammar/parser-constrained softmax masking.

    The estimator behaves like sklearn's LogisticRegression during training. At
    prediction time, it optionally accepts a per-row list of allowed SectionEnums
    and zeroes out probability mass for classes outside that list before choosing
    the argmax.

    Typical use from HearingParser:
        allowed_sections = classifier.allowed_sections_for_hearing(
            hearing=hearing,
            tokenizer=self.tokenizer,
            grammar=GRAMMAR,
            speaker_positions=speaker_positions,
            can_file_motions=can_file_motions,
            is_presenters=is_presenters,
        )
        y_hat = classifier.predict(X_transformed, allowed_sections=allowed_sections)
    """

    helper_class = MaskedSoftmaxHelper

    def predict(
        self,
        X: Any,
        allowed_sections: Optional[Sequence[Iterable[Any]]] = None,
        **kwargs: Any,
    ) -> np.ndarray:
        """Predict labels after applying an optional per-sample section mask.

        Extra kwargs are accepted for backward compatibility with older parser
        calls. If ``allowed_sections`` is omitted and a hearing/tokenizer is
        supplied, the classifier will attempt to build masks itself.
        """
        if (
            allowed_sections is None
            and "hearing" in kwargs
            and "tokenizer" in kwargs
        ):
            allowed_sections = self.allowed_sections_for_hearing(
                hearing=kwargs["hearing"],
                tokenizer=kwargs["tokenizer"],
                grammar=kwargs.get("grammar"),
                speaker_positions=kwargs.get("speaker_positions"),
                can_file_motions=kwargs.get("can_file_motions"),
                is_presenters=kwargs.get("is_presenters"),
            )

        probs = self.predict_proba_masked(X, allowed_sections=allowed_sections)
        return self.classes_[np.argmax(probs, axis=1)]

    def predict_proba_masked(
        self,
        X: Any,
        allowed_sections: Optional[Sequence[Iterable[Any]]] = None,
    ) -> np.ndarray:
        """Return class probabilities after masking and renormalizing."""
        probs = super().predict_proba(X)

        if allowed_sections is None:
            return probs

        if len(allowed_sections) != probs.shape[0]:
            raise ValueError(
                f"allowed_sections length ({len(allowed_sections)}) must match "
                f"number of rows in X ({probs.shape[0]})."
            )

        masked = probs.copy()
        class_keys = [self.helper_class._section_key(c) for c in self.classes_]

        for row_idx, allowed in enumerate(allowed_sections):
            allowed_keys = {self.helper_class._section_key(s) for s in allowed if s is not None}

            # Empty/unknown mask means "do not constrain this row".
            if not allowed_keys:
                continue

            keep = np.array([key in allowed_keys for key in class_keys], dtype=bool)

            # If the grammar/parser produced labels that are not in the trained
            # classifier classes, keep the unmasked classifier distribution.
            if not keep.any():
                continue

            masked[row_idx, ~keep] = 0.0
            denom = masked[row_idx].sum()

            # LogisticRegression probabilities are non-negative, but guard
            # against numerical/degenerate cases by falling back to a uniform
            # distribution over allowed trained classes.
            if denom > 0:
                masked[row_idx] /= denom
            else:
                masked[row_idx, keep] = 1.0 / keep.sum()

        return masked

    @classmethod
    def allowed_sections_for_hearing(
        cls,
        hearing: Any,
        tokenizer: Any,
        grammar: Any = None,
        speaker_positions: Optional[Sequence[Any]] = None,
        can_file_motions: Optional[Sequence[Any]] = None,
        is_presenters: Optional[Sequence[Any]] = None,
        max_parses: int = 2,
    ) -> List[List[Any]]:
        """Delegate hearing-mask construction to MaskedSoftmaxClassifierHelper."""
        return cls.helper_class.allowed_sections_for_hearing(
            hearing=hearing,
            tokenizer=tokenizer,
            grammar=grammar,
            speaker_positions=speaker_positions,
            can_file_motions=can_file_motions,
            is_presenters=is_presenters,
            max_parses=max_parses,
        )

    @classmethod
    def _section_key(cls, value: Any) -> str:
        """Return a stable section key for backward compatibility."""
        return cls.helper_class._section_key(value)