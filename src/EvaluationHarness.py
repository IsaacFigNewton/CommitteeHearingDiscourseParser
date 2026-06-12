from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Iterable, Any

import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, hamming_loss

from .dataclasses.Hearing import ParsedHearing
from .dataclasses.TaggedUtterance import TaggedUtterance

section_name_enum_map = dict()

def _json_safe(value: Any) -> Any:
    """
    Convert enums and other non-JSON-safe objects into serializable values.
    """
    if isinstance(value, Enum):
        return value.name
    return value


def _safe_vars(obj: Any) -> dict:
    """
    Like vars(obj), but converts enum values into readable strings.
    """
    return {k: _json_safe(v) for k, v in vars(obj).items()}


def store_tagged_samples(
    parsedhearings: Iterable[ParsedHearing],
    output_dir: str | Path = ".",
    csv_name: str = "tagged_utterances.csv",
    json_name: str = "tagged_utterances.json",
) -> pd.DataFrame:
    """
    Builds tagged utterance rows from parsed hearing objects, saves them as CSV
    and JSON, and returns the DataFrame.

    Expected structure:
        hearing.hid
        hearing.pid
        hearing.utterances

        utterance.uid
        utterance.text
        utterance.speakerpositionenum
        utterance.speakerroleenum
        utterance.sectionenum
    """

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    Tagged_utterances: list[dict] = []
    Tagged_utterances_Json: list[str] = []

    for h in parsedhearings:
        for section_name, section in vars(h).items():
            for u in section.utterances:
                speaker = h.speakers[u.pid]
                tagged_u = _safe_vars(
                    TaggedUtterance(
                        hid=h.hid,
                        pid=u.pid,
                        uid=u.uid,
                        is_legislator=section.is_legislator,
                        is_committee_member=speaker.is_committee_member,
                        is_bill_author=speaker.is_bill_author,
                        position=speaker.speaker_position,
                        role=speaker.speaker_role,
                        section=section_name_enum_map[section_name],
                    )
                )

            tagged_u["text"] = u.text

            Tagged_utterances.append(tagged_u)
            Tagged_utterances_Json.append(
                json.dumps(tagged_u, indent=4, default=lambda obj: _safe_vars(obj))
            )

    df = pd.DataFrame(Tagged_utterances)

    csv_path = output_dir / csv_name
    json_path = output_dir / json_name

    df.to_csv(csv_path, index=False)

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(Tagged_utterances_Json, f, indent=4)

    return df


def evaluate(
    model_sample_prediction_csv_path: str | Path,
    ground_truth_csv_path: str | Path,
) -> pd.Series:
    """
    Compares predicted speaker position, speaker role, and section labels against
    ground-truth labels.

    Required shared ID columns:
        hid
        uid

    Required label columns in both CSVs:
        speakerpositionenum
        speakerroleenum
        sectionenum
    """

    label_cols = [
        "speakerpositionenum",
        "speakerroleenum",
        "sectionenum",
    ]

    ground_truth = pd.read_csv(ground_truth_csv_path)
    predicted = pd.read_csv(model_sample_prediction_csv_path)

    required_cols = {"hid", "uid", *label_cols}

    missing_truth = required_cols - set(ground_truth.columns)
    missing_pred = required_cols - set(predicted.columns)

    if missing_truth:
        raise ValueError(f"Ground-truth CSV is missing columns: {sorted(missing_truth)}")

    if missing_pred:
        raise ValueError(f"Prediction CSV is missing columns: {sorted(missing_pred)}")

    merged = ground_truth.merge(
        predicted,
        on=["hid", "uid"],
        suffixes=("_true", "_pred"),
        how="inner",
    )

    if merged.empty:
        raise ValueError("No matching rows found between prediction and ground truth on hid, uid.")

    scores: dict[str, float | int] = {
        "num_ground_truth_rows": len(ground_truth),
        "num_prediction_rows": len(predicted),
        "num_matched_rows": len(merged),
    }

    for col in label_cols:
        y_true = merged[f"{col}_true"].astype(str)
        y_pred = merged[f"{col}_pred"].astype(str)

        scores[f"{col}_accuracy"] = accuracy_score(y_true, y_pred)
        scores[f"{col}_precision_macro"] = precision_score(
            y_true,
            y_pred,
            average="macro",
            zero_division=0,
        )
        scores[f"{col}_recall_macro"] = recall_score(
            y_true,
            y_pred,
            average="macro",
            zero_division=0,
        )
        scores[f"{col}_f1_macro"] = f1_score(
            y_true,
            y_pred,
            average="macro",
            zero_division=0,
        )

    true_label_df = merged[[f"{col}_true" for col in label_cols]].copy()
    pred_label_df = merged[[f"{col}_pred" for col in label_cols]].copy()

    true_label_df.columns = label_cols
    pred_label_df.columns = label_cols

    combined = pd.concat(
        [true_label_df.assign(_source="true"), pred_label_df.assign(_source="pred")],
        ignore_index=True,
    )

    onehot = pd.get_dummies(combined[label_cols], columns=label_cols)

    y_true_onehot = onehot.iloc[: len(true_label_df)].to_numpy()
    y_pred_onehot = onehot.iloc[len(true_label_df) :].to_numpy()

    scores["onehot_accuracy"] = accuracy_score(y_true_onehot, y_pred_onehot)
    scores["onehot_hamming_loss"] = hamming_loss(y_true_onehot, y_pred_onehot)
    scores["onehot_precision_micro"] = precision_score(
        y_true_onehot,
        y_pred_onehot,
        average="micro",
        zero_division=0,
    )
    scores["onehot_recall_micro"] = recall_score(
        y_true_onehot,
        y_pred_onehot,
        average="micro",
        zero_division=0,
    )
    scores["onehot_f1_micro"] = f1_score(
        y_true_onehot,
        y_pred_onehot,
        average="micro",
        zero_division=0,
    )

    return pd.Series(scores)