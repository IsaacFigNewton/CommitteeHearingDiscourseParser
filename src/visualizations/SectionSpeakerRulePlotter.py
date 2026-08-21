from collections import defaultdict
from typing import List, Union, Tuple, get_args
from enum import Enum

import matplotlib.pyplot as plt

from ..grammar.Grammar import Rule
from src.enums.SectionEnum import SectionEnum
from src.speakers.enums.SpeakerPositionEnum import SpeakerPositionEnum


class SectionSpeakerRulePlotter:
    def __init__(self,
            grammar: List[Rule],
        ):
        self.grammar = grammar
        self.ordered_sections = list(SectionEnum)
        
        self.section_speaker_map = defaultdict(list)
        for rule in self.grammar:
            # if it's a binary terminal production rule
            if type(rule[1]) == tuple and type(rule[1][0]) == SpeakerPositionEnum:
                self.section_speaker_map[rule[0]].append(rule[1][0])
                self.section_speaker_map[rule[0]].append(rule[1][1])
            # if it's a unary terminal production rule
            elif type(rule[1]) == SpeakerPositionEnum:
                self.section_speaker_map[rule[0]].append(rule[1])
        

    def plot(self) -> None:
        all_speakers = set()
        for speakers in self.section_speaker_map.values():
            all_speakers.update(speakers)

        sorted_speakers = sorted(
            all_speakers,
            key=lambda speaker: speaker.value,
            reverse=True,
        )

        speaker_to_position = {
            speaker: index
            for index, speaker in enumerate(sorted_speakers)
        }

        position_to_speaker = {
            position: speaker
            for speaker, position in speaker_to_position.items()
        }

        print(
            f"Found {len(self.section_speaker_map)} sections with speaker position rules:"
        )

        for section in self.ordered_sections:
            speakers = self.section_speaker_map[section]
            speaker_names = [
                f"{speaker.name}({speaker.value})"
                for speaker in sorted(
                    speakers,
                    key=lambda speaker: speaker.value,
                    reverse=True,
                )
            ]
            print(f"  {section.name}: {speaker_names}")

        fig, ax = plt.subplots(figsize=(14, 8))

        bar_height = 0.6
        bar_width = 0.8
        label_size = 9
        axis_label_size = 12
        title_size = 14

        num_sections = len(self.ordered_sections)
        num_speakers = len(speaker_to_position)

        speaker_colors = plt.get_cmap("hsv", num_speakers)

        for section_index, section in enumerate(self.ordered_sections):
            speakers = self.section_speaker_map[section]

            positions = sorted(
                speaker_to_position[speaker]
                for speaker in speakers
            )

            for position in positions:
                color = speaker_colors(position)

                ax.barh(
                    y=position,
                    width=bar_width,
                    left=section_index - bar_width / 2,
                    height=bar_height,
                    color=color,
                    alpha=0.7,
                )

        ax.set_xticks(range(num_sections))
        ax.set_xticklabels(
            [section.name for section in self.ordered_sections],
            rotation=0,
            ha="center",
            fontsize=label_size,
        )

        ax.set_yticks(range(num_speakers))
        ax.set_yticklabels(
            [
                position_to_speaker[position].name
                for position in range(num_speakers)
            ],
            fontsize=label_size,
        )

        ax.set_xlabel("Section", fontsize=axis_label_size)
        ax.set_ylabel("Speaker Position", fontsize=axis_label_size)
        ax.set_title(
            "Grammar Rules: Valid SpeakerPositionEnum by SectionEnum",
            fontsize=title_size,
        )

        ax.grid(axis="y", alpha=0.8, linestyle="-")

        ax.set_xlim(-0.5, num_sections - 0.5)
        ax.set_ylim(-0.5, num_speakers - 0.5)

        plt.tight_layout()
        plt.show()