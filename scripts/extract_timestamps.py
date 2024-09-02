from pathlib import Path

import numpy as np
import pandas as pd


def read_timetable(
    timetable_path: Path, output_path: Path, subjectid: str, sequence_label: str
):
    dframe = pd.read_csv(timetable_path, sep="\t")
    subject_sequence_entries = (dframe["subject"] == subjectid) & (
        dframe["sequence_label"] == sequence_label
    )
    acq_times = dframe[subject_sequence_entries]["acquisition_relative_injection"]
    times = np.array(acq_times)
    assert len(times) > 0
    np.savetxt(output_path, np.maximum(0.0, times))


if __name__ == "__main__":
    import typer

    typer.run(read_timetable)
