"""Unit tests for src.ClassifierPipeline.

Focus: the contract evaluate_model.ipynb relies on --

    test_df = test_df.sort_values(by=['hearing_group', 'uid']).reset_index(drop=True)
    pred = parser.predict(X_test)
    classification_report(y_test, pred, labels=[s.name for s in SectionEnum])

i.e. ``predict(X)`` must return exactly one label per row of ``X``, in the
order of ``X`` sorted by (hearing_group, uid). The sklearn Pipeline and the
grammar parser are mocked so these tests exercise only the glue logic.
"""
import unittest
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from src import ClassifierPipeline as pipeline_module
from src.ClassifierPipeline import ClassifierPipeline
from src.classifier.Classifier import Classifier
from src.classifier.Masker import Masker
from src.constants.constants import FEATURE_COLS, NUM_COLS, TEXT_COL, TOKEN_COL
from src.enums.SectionEnum import SectionEnum
from src.speakers.enums.SpeakerPositionEnum import SpeakerPositionEnum

SECTIONS = list(SectionEnum)
SPEAKERS = list(SpeakerPositionEnum)


def make_df(rows):
    """Build a harness-shaped DataFrame from (hearing_group, uid, speaker_token) tuples.

    TEXT_COL is set to a unique marker "<group>:<uid>" so a mocked model can echo
    it back and we can check which input row each output label came from.
    """
    records = []
    for group, uid, tok in rows:
        rec = {c: (0.0 if c in NUM_COLS else "x") for c in FEATURE_COLS}
        rec[TEXT_COL] = f"{group}:{uid}"
        rec[TOKEN_COL] = tok
        rec["uid"] = uid
        rec["hearing_group"] = group
        records.append(rec)
    return pd.DataFrame.from_records(records)


def echo_text(X):
    """Mock model.predict: returns the TEXT_COL marker of each row as its label."""
    return np.asarray(X[TEXT_COL].tolist(), dtype=object)


class PipelineTestBase(unittest.TestCase):
    """Builds a ClassifierPipeline whose heavy dependencies are replaced with mocks."""

    def setUp(self):
        tagger_patch = patch.object(pipeline_module, "HearingTagger", MagicMock())
        tagger_patch.start()
        self.addCleanup(tagger_patch.stop)

        self.tok_map = {SPEAKERS[0].value: SPEAKERS[0], SPEAKERS[1].value: SPEAKERS[1]}
        map_patch = patch.object(pipeline_module, "TERMINAL_STR_TOK_MAP", self.tok_map)
        map_patch.start()
        self.addCleanup(map_patch.stop)

        self.parser = MagicMock(name="parser")
        self.parser.get_all_parses_as_nltk_trees.return_value = []
        parser_patch = patch.object(ClassifierPipeline, "parser", self.parser)
        parser_patch.start()
        self.addCleanup(parser_patch.stop)

        self.pipe = ClassifierPipeline(masking=True, smoothing=False)

        self.model = MagicMock(name="sklearn_pipeline")
        self.model.predict.side_effect = echo_text
        self.pipe.model = self.model

        self.helper = MagicMock(name="masking_helper")
        # one empty mask per utterance, aligned with token_seq length
        self.helper.allowed_sections_for_hearing.side_effect = (
            lambda token_seq, parse_trees: [[] for _ in token_seq]
        )
        self.pipe.masking_helper = self.helper

    def class_mask_calls(self):
        return [
            c.kwargs["masker__class_mask"]
            for c in self.model.set_params.call_args_list
            if "masker__class_mask" in c.kwargs
        ]


class TestPredictOutputAlignment(PipelineTestBase):
    def test_returns_ndarray_with_one_label_per_input_row(self):
        X = make_df([("h1", 1, "x"), ("h1", 2, "x"), ("h2", 1, "x"), ("h2", 2, "x"), ("h2", 3, "x")])
        pred = self.pipe.predict(X)
        self.assertIsInstance(pred, np.ndarray)
        self.assertEqual(pred.shape, (len(X),))

    def test_harness_sorted_input_aligns_row_for_row(self):
        """This is the exact ordering the notebook uses before calling predict()."""
        rows = [("h1", 1, "x"), ("h1", 2, "x"), ("h1", 3, "x"), ("h2", 10, "x"), ("h2", 11, "x")]
        X = make_df(rows).sort_values(["hearing_group", "uid"]).reset_index(drop=True)
        pred = self.pipe.predict(X)
        np.testing.assert_array_equal(pred, X[TEXT_COL].to_numpy())

    def test_string_hearing_group_sorting_matches_notebook(self):
        """Groups are bid_hid strings in the notebook; lexical order must round-trip."""
        rows = [("CA_AB10_100", 2, "x"), ("CA_AB10_100", 1, "x"), ("CA_AB2_50", 7, "x"), ("CA_AB2_50", 3, "x")]
        X = make_df(rows).sort_values(["hearing_group", "uid"]).reset_index(drop=True)
        pred = self.pipe.predict(X)
        np.testing.assert_array_equal(pred, X[TEXT_COL].to_numpy())

    def test_rows_within_a_hearing_are_predicted_in_uid_order(self):
        """predict() sorts each hearing by uid internally, so if the caller passes
        an unsorted hearing the output is in uid order, NOT input order."""
        X = make_df([("h1", 3, "x"), ("h1", 1, "x"), ("h1", 2, "x")])
        pred = self.pipe.predict(X)
        np.testing.assert_array_equal(pred, ["h1:1", "h1:2", "h1:3"])
        self.assertFalse(np.array_equal(pred, X[TEXT_COL].to_numpy()))

    def test_hearings_are_emitted_in_order_of_first_appearance(self):
        """If hearings are interleaved in X, output is grouped by hearing and no
        longer aligned with X's rows. The harness must sort before predicting."""
        X = make_df([("h1", 1, "x"), ("h2", 1, "x"), ("h1", 2, "x"), ("h2", 2, "x")])
        pred = self.pipe.predict(X)
        np.testing.assert_array_equal(pred, ["h1:1", "h1:2", "h2:1", "h2:2"])
        self.assertFalse(np.array_equal(pred, X[TEXT_COL].to_numpy()))

    def test_predict_is_called_once_per_hearing_with_only_feature_columns(self):
        X = make_df([("h1", 1, "x"), ("h1", 2, "x"), ("h2", 1, "x")])
        self.pipe.predict(X)
        self.assertEqual(self.model.predict.call_count, 2)
        for call in self.model.predict.call_args_list:
            passed = call.args[0]
            self.assertEqual(list(passed.columns), FEATURE_COLS)
            self.assertNotIn("hearing_group", passed.columns)

    def test_single_row_hearing(self):
        X = make_df([("h1", 1, "x")])
        np.testing.assert_array_equal(self.pipe.predict(X), ["h1:1"])


class TestClassMaskAlignment(PipelineTestBase):
    def test_class_mask_has_one_entry_per_row_of_each_hearing(self):
        X = make_df([("h1", 1, "x"), ("h1", 2, "x"), ("h1", 3, "x"), ("h2", 1, "x")])
        self.pipe.predict(X)
        masks = self.class_mask_calls()
        self.assertEqual([len(m) for m in masks], [3, 1])

    def test_class_mask_is_set_before_predict_for_each_hearing(self):
        X = make_df([("h1", 1, "x"), ("h2", 1, "x")])
        order = []
        self.model.set_params.side_effect = lambda **kw: order.append("set")
        self.model.predict.side_effect = lambda X: (order.append("predict"), echo_text(X))[1]
        self.pipe.predict(X)
        self.assertEqual(order, ["set", "predict", "set", "predict"])

    def test_masking_disabled_never_sets_class_mask(self):
        self.pipe.masking = False
        self.pipe.predict(make_df([("h1", 1, "x"), ("h1", 2, "x")]))
        self.assertEqual(self.class_mask_calls(), [])

    def test_token_seq_is_built_in_uid_order_via_terminal_map(self):
        s0, s1 = SPEAKERS[0].value, SPEAKERS[1].value
        X = make_df([("h1", 2, s1), ("h1", 1, s0), ("h1", 3, "UNKNOWN_TOKEN"), ("h1", 4, np.nan)])
        self.pipe.predict(X)
        token_seq = self.helper.allowed_sections_for_hearing.call_args.kwargs["token_seq"]
        # sorted by uid: 1->s0, 2->s1, 3->unmapped, 4->nan
        self.assertEqual(token_seq, [SPEAKERS[0], SPEAKERS[1], None, None])

    def test_token_seq_length_matches_hearing_rows(self):
        X = make_df([("h1", i, "x") for i in range(9)])
        self.pipe.predict(X)
        token_seq = self.helper.allowed_sections_for_hearing.call_args.kwargs["token_seq"]
        self.assertEqual(len(token_seq), 9)

    def test_parse_trees_forwarded_to_helper(self):
        trees = ["tree_a", "tree_b"]
        self.parser.get_all_parses_as_nltk_trees.return_value = trees
        self.pipe.predict(make_df([("h1", 1, "x")]))
        self.parser.get_all_parses_as_nltk_trees.assert_called_once()
        self.assertEqual(
            self.parser.get_all_parses_as_nltk_trees.call_args.kwargs["max_parses"],
            self.pipe.max_parses,
        )
        kwargs = self.helper.allowed_sections_for_hearing.call_args.kwargs
        self.assertEqual(kwargs["parse_trees"], trees)

    def test_parser_failure_falls_back_to_empty_parse_trees(self):
        self.parser.get_all_parses_as_nltk_trees.side_effect = RuntimeError("no parse")
        pred = self.pipe.predict(make_df([("h1", 1, "x"), ("h1", 2, "x")]))
        kwargs = self.helper.allowed_sections_for_hearing.call_args.kwargs
        self.assertEqual(kwargs["parse_trees"], [])
        self.assertEqual(len(pred), 2)

    def test_helper_mask_is_passed_through_unchanged(self):
        expected = [[SECTIONS[0]], [SECTIONS[1]]]
        self.helper.allowed_sections_for_hearing.side_effect = None
        self.helper.allowed_sections_for_hearing.return_value = expected
        self.pipe.predict(make_df([("h1", 1, "x"), ("h1", 2, "x")]))
        self.assertEqual(self.class_mask_calls(), [expected])


class TestSmoothing(PipelineTestBase):
    def setUp(self):
        super().setUp()
        self.pipe.smoothing = True

    def _run_with_labels(self, labels):
        self.model.predict.side_effect = lambda X: np.asarray(labels, dtype=object)
        X = make_df([("h1", i, "x") for i in range(len(labels))])
        return list(self.pipe.predict(X))

    def test_isolated_label_between_identical_neighbours_is_replaced(self):
        self.assertEqual(self._run_with_labels(["A", "B", "A"]), ["A", "A", "A"])

    def test_edges_are_never_smoothed(self):
        self.assertEqual(self._run_with_labels(["B", "A", "A", "B"]), ["B", "A", "A", "B"])

    def test_runs_of_two_are_preserved(self):
        self.assertEqual(self._run_with_labels(["A", "B", "B", "A"]), ["A", "B", "B", "A"])

    def test_smoothing_preserves_length(self):
        labels = ["A", "B", "A", "C", "A", "A", "B", "A"]
        self.assertEqual(len(self._run_with_labels(labels)), len(labels))

    def test_smoothing_is_a_single_pass(self):
        # A single pass: index 1 fixed to A (neighbours A, A), index 3 not fixed
        # because index 2's original value B != index 4's value C.
        self.assertEqual(
            self._run_with_labels(["A", "B", "A", "B", "C"]), ["A", "A", "A", "B", "C"]
        )

    def test_smoothing_does_not_leak_across_hearings(self):
        # Each hearing is smoothed independently; a 1-row hearing between two
        # identical rows of another hearing must not be altered.
        self.model.predict.side_effect = echo_text
        X = make_df([("h1", 1, "x"), ("h2", 1, "x"), ("h1", 2, "x")])
        pred = self.pipe.predict(X)
        np.testing.assert_array_equal(pred, ["h1:1", "h1:2", "h2:1"])


class TestFit(PipelineTestBase):
    def test_fit_forwards_X_and_y_to_model(self):
        X, y = MagicMock(name="X"), MagicMock(name="y")
        self.pipe.fit(X, y)
        self.model.fit.assert_called_once_with(X, y)

    def test_fit_sets_masker_classes_in_section_enum_order(self):
        self.pipe.fit(MagicMock(), MagicMock())
        kwargs = self.model.set_params.call_args.kwargs
        np.testing.assert_array_equal(kwargs["masker__classes_"], [s.value for s in SECTIONS])

    def test_classes_attribute_matches_section_enum_values(self):
        np.testing.assert_array_equal(ClassifierPipeline.classes_, [s.value for s in SECTIONS])


class TestMaskerAndClassifierClassOrderAgree(unittest.TestCase):
    """The Masker decodes ``argmax`` with the ``classes_`` ClassifierPipeline.fit()
    assigns it (SectionEnum declaration order). The probability columns it
    receives are ordered by the *fitted* estimator's ``classes_`` (sklearn sorts
    labels). Unless these two arrays are identical, every predicted label is
    permuted before it reaches classification_report.

    Uses a real (features-free) Pipeline of Classifier -> Masker so the check
    reflects actual sklearn behaviour rather than a mock.
    """

    def test_masker_classes_equal_fitted_classifier_classes(self):
        with patch.object(pipeline_module, "HearingTagger", MagicMock()):
            pipe = ClassifierPipeline()
        pipe.model = Pipeline(
            [
                ("classifier", Classifier(base_estimator=LogisticRegression(max_iter=200))),
                ("masker", Masker()),
            ]
        )
        n = len(SECTIONS)
        # one clearly separable feature vector per class, repeated
        X = np.tile(np.eye(n), (3, 1))
        y = np.array([s.value for s in SECTIONS] * 3)
        pipe.fit(X, y)

        fitted = pipe.model.named_steps["classifier"].classes_
        masker = pipe.model.named_steps["masker"].classes_
        np.testing.assert_array_equal(
            masker,
            fitted,
            err_msg="Masker.classes_ order differs from the fitted classifier's "
            "predict_proba column order; argmax labels will be permuted.",
        )

    def test_unmasked_predict_round_trips_training_labels(self):
        with patch.object(pipeline_module, "HearingTagger", MagicMock()):
            pipe = ClassifierPipeline()
        pipe.model = Pipeline(
            [
                ("classifier", Classifier(base_estimator=LogisticRegression(max_iter=200))),
                ("masker", Masker()),
            ]
        )
        n = len(SECTIONS)
        X = np.tile(np.eye(n) * 10, (3, 1))
        y = np.array([s.value for s in SECTIONS] * 3)
        pipe.fit(X, y)
        np.testing.assert_array_equal(pipe.model.predict(X), y)


if __name__ == "__main__":
    unittest.main()
