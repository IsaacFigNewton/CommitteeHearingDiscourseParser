"""Unit tests for src.classifier.MaskedSoftmaxHelper.

Focus: the returned mask list must have exactly one entry per utterance and
each entry must be aligned with the utterance at the same index.
"""
import unittest
from unittest.mock import patch

import numpy as np
from nltk.tree import Tree

from src.classifier import MaskedSoftmaxHelper as helper_module
from src.classifier.MaskedSoftmaxHelper import MaskedSoftmaxHelper
from src.enums.SectionEnum import SectionEnum
from src.speakers.enums.SpeakerPositionEnum import SpeakerPositionEnum

SECTIONS = list(SectionEnum)
SPEAKERS = list(SpeakerPositionEnum)
CLASSES = np.array([s.value for s in SECTIONS])


def _section_tree(sections_per_leaf):
    """Build a tree ROOT -> (section_i -> leaf_i) so each leaf has one SectionEnum ancestor."""
    return Tree("ROOT", [Tree(sec, [f"leaf{i}"]) for i, sec in enumerate(sections_per_leaf)])


class TestFallbackMasks(unittest.TestCase):
    def setUp(self):
        self.reachable = {
            SPEAKERS[0]: {SECTIONS[0], SECTIONS[1]},
            SPEAKERS[1]: {SECTIONS[2]},
        }
        patcher = patch.object(helper_module, "SPEAKER_REACHABLE_SECTIONS", self.reachable)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.helper = MaskedSoftmaxHelper(CLASSES)

    def test_no_parse_trees_uses_speaker_reachable_sections(self):
        seq = [SPEAKERS[0], SPEAKERS[1], SPEAKERS[0]]
        masks = self.helper.allowed_sections_for_hearing(seq, parse_trees=None)
        self.assertEqual(len(masks), 3)
        self.assertEqual(set(masks[0]), {SECTIONS[0], SECTIONS[1]})
        self.assertEqual(set(masks[1]), {SECTIONS[2]})
        self.assertEqual(set(masks[2]), {SECTIONS[0], SECTIONS[1]})

    def test_empty_tree_list_behaves_like_none(self):
        seq = [SPEAKERS[0], SPEAKERS[1]]
        self.assertEqual(
            [set(m) for m in self.helper.allowed_sections_for_hearing(seq, parse_trees=[])],
            [set(m) for m in self.helper.allowed_sections_for_hearing(seq, parse_trees=None)],
        )

    def test_unknown_or_none_speaker_gets_empty_mask(self):
        seq = [None, SPEAKERS[2]]  # SPEAKERS[2] not in patched reachable map
        masks = self.helper.allowed_sections_for_hearing(seq)
        self.assertEqual(masks, [[], []])

    def test_mask_count_equals_token_count(self):
        for n in (0, 1, 5, 17):
            seq = [SPEAKERS[i % 2] for i in range(n)]
            self.assertEqual(len(self.helper.allowed_sections_for_hearing(seq)), n)

    def test_fallback_used_when_tree_leaf_count_mismatches_utterances(self):
        """A tree with the wrong number of leaves cannot be aligned positionally;
        the helper must fall back rather than emit a misaligned mask."""
        seq = [SPEAKERS[0], SPEAKERS[1], SPEAKERS[0]]
        tree = _section_tree([SECTIONS[3], SECTIONS[3]])  # 2 leaves for 3 utterances
        masks = self.helper.allowed_sections_for_hearing(seq, parse_trees=[tree])
        self.assertEqual(set(masks[0]), {SECTIONS[0], SECTIONS[1]})
        self.assertEqual(set(masks[1]), {SECTIONS[2]})


class TestParseTreeMasks(unittest.TestCase):
    def setUp(self):
        self.helper = MaskedSoftmaxHelper(CLASSES)
        self.seq = [SPEAKERS[0], SPEAKERS[1], SPEAKERS[0], SPEAKERS[1]]

    def test_positional_alignment_maps_leaf_i_to_utterance_i(self):
        tree = _section_tree([SECTIONS[0], SECTIONS[1], SECTIONS[2], SECTIONS[3]])
        masks = self.helper.allowed_sections_for_hearing(self.seq, parse_trees=[tree])
        self.assertEqual(masks, [[SECTIONS[0]], [SECTIONS[1]], [SECTIONS[2]], [SECTIONS[3]]])

    def test_multiple_trees_are_unioned_per_utterance(self):
        t1 = _section_tree([SECTIONS[0]] * 4)
        t2 = _section_tree([SECTIONS[1]] * 4)
        masks = self.helper.allowed_sections_for_hearing(self.seq, parse_trees=[t1, t2])
        for m in masks:
            self.assertEqual(set(m), {SECTIONS[0], SECTIONS[1]})

    def test_parse_trees_take_precedence_over_fallback(self):
        tree = _section_tree([SECTIONS[4]] * 4)
        with patch.object(
            helper_module, "SPEAKER_REACHABLE_SECTIONS", {s: {SECTIONS[0]} for s in SPEAKERS}
        ):
            masks = self.helper.allowed_sections_for_hearing(self.seq, parse_trees=[tree])
        self.assertTrue(all(m == [SECTIONS[4]] for m in masks))

    def test_leaf_without_section_ancestor_leaves_that_utterance_empty(self):
        tree = Tree(
            "ROOT",
            [
                Tree(SECTIONS[0], ["leaf0"]),
                Tree("NONSECTION", ["leaf1"]),  # no SectionEnum on this path
                Tree(SECTIONS[2], ["leaf2"]),
                Tree(SECTIONS[3], ["leaf3"]),
            ],
        )
        masks = self.helper.allowed_sections_for_hearing(self.seq, parse_trees=[tree])
        self.assertEqual(masks[1], [])
        self.assertEqual(masks[0], [SECTIONS[0]])

    def test_deepest_section_ancestor_wins(self):
        tree = Tree("ROOT", [Tree(SECTIONS[0], [Tree(SECTIONS[1], ["leaf0"])])])
        masks = self.helper.allowed_sections_for_hearing([SPEAKERS[0]], parse_trees=[tree])
        self.assertEqual(masks, [[SECTIONS[1]]])

    def test_leaf_records_enumerate_leaves_left_to_right(self):
        tree = _section_tree([SECTIONS[0], SECTIONS[1], SECTIONS[2]])
        records = list(MaskedSoftmaxHelper._iter_leaf_records(tree))
        self.assertEqual([pos for pos, _, _ in records], [0, 1, 2])
        self.assertEqual([leaf for _, leaf, _ in records], ["leaf0", "leaf1", "leaf2"])

    def test_iter_leaf_records_default_ancestors_not_shared_between_calls(self):
        tree = _section_tree([SECTIONS[0]])
        first = list(MaskedSoftmaxHelper._iter_leaf_records(tree))
        second = list(MaskedSoftmaxHelper._iter_leaf_records(tree))
        self.assertEqual(first[0][2], second[0][2])
        self.assertEqual(first[0][2], ("ROOT", SECTIONS[0]))


class TestFirstSectionLabel(unittest.TestCase):
    def test_returns_none_when_no_section(self):
        self.assertIsNone(MaskedSoftmaxHelper._first_section_label(["ROOT", "X", None]))

    def test_returns_last_section_in_path(self):
        labels = ["ROOT", SECTIONS[0], "NT", SECTIONS[2]]
        self.assertIs(MaskedSoftmaxHelper._first_section_label(labels), SECTIONS[2])


if __name__ == "__main__":
    unittest.main()
