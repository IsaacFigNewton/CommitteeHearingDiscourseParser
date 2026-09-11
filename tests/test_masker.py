"""Unit tests for src.classifier.Masker.

Focus: row/column alignment between the incoming probability matrix, the
per-row class mask, and the ``classes_`` array used to decode argmax.
"""
import unittest

import numpy as np

from src.classifier.Masker import Masker
from src.enums.SectionEnum import SectionEnum

SECTIONS = list(SectionEnum)
CLASSES = np.array([s.value for s in SECTIONS])
N_CLASSES = len(CLASSES)


def _one_hot_row(idx):
    row = np.zeros(N_CLASSES)
    row[idx] = 1.0
    return row


class TestMaskerWithoutMask(unittest.TestCase):
    def test_fit_is_noop_and_returns_self(self):
        m = Masker()
        self.assertIs(m.fit(np.zeros((2, N_CLASSES)), None), m)

    def test_predict_proba_passthrough_when_no_mask(self):
        probs = np.random.default_rng(0).dirichlet(np.ones(N_CLASSES), size=4)
        m = Masker(classes_=CLASSES)
        np.testing.assert_array_equal(m.predict_proba(probs), probs)

    def test_predict_is_argmax_over_classes_when_no_mask(self):
        probs = np.vstack([_one_hot_row(i) for i in range(N_CLASSES)])
        m = Masker(classes_=CLASSES)
        np.testing.assert_array_equal(m.predict(probs), CLASSES)

    def test_predict_returns_one_label_per_input_row(self):
        probs = np.random.default_rng(1).dirichlet(np.ones(N_CLASSES), size=7)
        labels = Masker(classes_=CLASSES).predict(probs)
        self.assertEqual(labels.shape, (7,))

    def test_predict_raises_without_classes(self):
        with self.assertRaises(ValueError):
            Masker().predict(np.ones((1, N_CLASSES)) / N_CLASSES)


class TestMaskerApplyMasking(unittest.TestCase):
    def setUp(self):
        self.uniform = np.full((3, N_CLASSES), 1.0 / N_CLASSES)

    def test_mask_length_must_match_rows(self):
        m = Masker(classes_=CLASSES, class_mask=[[SECTIONS[0]]] * 2)
        with self.assertRaisesRegex(ValueError, "must match"):
            m.predict_proba(self.uniform)  # 3 rows, 2 masks

    def test_apply_masking_requires_classes(self):
        m = Masker(class_mask=[[SECTIONS[0]]] * 3)
        with self.assertRaises(ValueError):
            m.predict_proba(self.uniform)

    def test_disallowed_classes_are_zeroed_and_row_renormalised(self):
        allowed = [SECTIONS[0], SECTIONS[1]]
        m = Masker(classes_=CLASSES, class_mask=[allowed] * 3)
        out = m.predict_proba(self.uniform)

        keep = np.isin(CLASSES, [s.value for s in allowed])
        self.assertTrue(np.all(out[:, ~keep] == 0.0))
        np.testing.assert_allclose(out.sum(axis=1), 1.0)
        np.testing.assert_allclose(out[:, keep], 0.5)

    def test_input_matrix_is_not_mutated(self):
        m = Masker(classes_=CLASSES, class_mask=[[SECTIONS[0]]] * 3)
        before = self.uniform.copy()
        m.predict_proba(self.uniform)
        np.testing.assert_array_equal(self.uniform, before)

    def test_rows_with_none_or_empty_mask_are_left_untouched(self):
        m = Masker(classes_=CLASSES, class_mask=[None, [], [None]])
        out = m.predict_proba(self.uniform)
        np.testing.assert_array_equal(out, self.uniform)

    def test_mask_is_applied_per_row_not_globally(self):
        """Row i must get mask i -- a misaligned mask would silently corrupt labels."""
        probs = np.vstack([_one_hot_row(0), _one_hot_row(1), _one_hot_row(2)])
        # Force each row to a *different* class than its argmax by masking
        mask = [[SECTIONS[1]], [SECTIONS[2]], [SECTIONS[0]]]
        # Give every row a little mass everywhere so renormalisation is possible
        probs = probs * 0.9 + 0.1 / N_CLASSES
        labels = Masker(classes_=CLASSES, class_mask=mask).predict(probs)
        np.testing.assert_array_equal(
            labels, [SECTIONS[1].value, SECTIONS[2].value, SECTIONS[0].value]
        )

    def test_mask_referencing_unknown_class_raises(self):
        class Fake:
            value = "NOT_A_REAL_SECTION"

        m = Masker(classes_=CLASSES, class_mask=[[Fake()]] * 3)
        with self.assertRaises(ValueError):
            m.predict_proba(self.uniform)

    def test_degenerate_row_raises(self):
        # Row has zero probability on the only allowed class
        probs = np.vstack([_one_hot_row(0)])
        m = Masker(classes_=CLASSES, class_mask=[[SECTIONS[1]]])
        with self.assertRaisesRegex(ValueError, "Degenerate"):
            m.predict_proba(probs)

    def test_masked_argmax_decodes_against_classes_array(self):
        probs = np.random.default_rng(2).dirichlet(np.ones(N_CLASSES), size=5)
        mask = [[SECTIONS[i % N_CLASSES]] for i in range(5)]
        labels = Masker(classes_=CLASSES, class_mask=mask).predict(probs)
        expected = [SECTIONS[i % N_CLASSES].value for i in range(5)]
        np.testing.assert_array_equal(labels, expected)


class TestMaskerAlignmentWithClassifierColumns(unittest.TestCase):
    """The Masker decodes argmax with *its own* classes_, but the columns of the
    probability matrix follow the *fitted classifier's* classes_ (which sklearn
    sorts lexically). These must be the same array, in the same order, or labels
    are permuted. ClassifierPipeline currently sets the masker's classes_ from
    SectionEnum declaration order, so this test documents the required invariant."""

    def test_decoding_with_permuted_classes_yields_wrong_labels(self):
        sorted_classes = np.array(sorted(CLASSES))
        if np.array_equal(sorted_classes, CLASSES):
            self.skipTest("SectionEnum declaration order already equals sorted order")
        probs = np.vstack([_one_hot_row(i) for i in range(N_CLASSES)])  # columns in enum order
        wrong = Masker(classes_=sorted_classes).predict(probs)
        right = Masker(classes_=CLASSES).predict(probs)
        self.assertFalse(np.array_equal(wrong, right))
        np.testing.assert_array_equal(right, CLASSES)


class TestMaskerLabelsMatchEvaluationHarness(unittest.TestCase):
    """evaluate_model.ipynb passes ``labels=[s.name for s in SectionEnum]`` to
    classification_report, while the pipeline emits ``s.value``. If name != value
    the report silently scores every prediction as wrong."""

    def test_emitted_labels_are_in_harness_label_order(self):
        harness_labels = {s.name for s in SectionEnum}
        probs = np.vstack([_one_hot_row(i) for i in range(N_CLASSES)])
        emitted = set(Masker(classes_=CLASSES).predict(probs))
        self.assertTrue(
            emitted <= harness_labels,
            f"Predicted labels {emitted - harness_labels} are not in the "
            f"label_order used by classification_report ({harness_labels})",
        )


if __name__ == "__main__":
    unittest.main()
