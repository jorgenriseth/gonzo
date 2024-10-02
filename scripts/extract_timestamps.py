from pathlib import Path

import numpy as np
import pandas as pd


def extract_sequence_timestamps(
    timetable_path: Path, output_path: Path, subject: str, sequence_label: str
):
    try:
        timetable = pd.read_csv(timetable_path, sep="\t")
    except pd.errors.EmptyDataError:
        raise RuntimeError(f"Timetable-file {timetable_path} is empty.")
    subject_sequence_entries = (timetable["subject"] == subject) & (
        timetable["sequence_label"] == sequence_label
    )
    try:
        acq_times = timetable[subject_sequence_entries][
            "acquisition_relative_injection"
        ]
    except ValueError as e:
        print(timetable)
        print(subject, sequence_label)
        print(subject_sequence_entries)
        raise e
    times = np.array(acq_times)
    assert len(times) > 0, f"Couldn't find time for {subject}: {sequence_label}"
    np.savetxt(output_path, np.maximum(0.0, times))


if __name__ == "__main__":
    import typer

    typer.run(extract_sequence_timestamps)
