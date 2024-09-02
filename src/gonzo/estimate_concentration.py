from pathlib import Path
from typing import Optional

import numpy as np

from gonzo.simple_mri import load_mri, save_mri, SimpleMRI


def concentration_from_T1(T1: np.ndarray, T1_0: np.ndarray, r1: float) -> np.ndarray:
    C = 1 / r1 * (1 / T1 - 1 / T1_0)
    return C


def concentration_from_R1(R1: np.ndarray, R1_0: np.ndarray, r1: float) -> np.ndarray:
    C = 1 / r1 * (R1 - R1_0)
    return C


def main(
    input_path: Path,
    reference_path: Path,
    output_path: Path,
    r1: float,
    mask_path: Optional[Path] = None,
):
    T1_mri = load_mri(input_path, np.single)
    T10_mri = load_mri(reference_path, np.single)
    assert np.allclose(
        T1_mri.affine, T10_mri.affine
    ), "Affine transformations differ, are you sure the  baseline and T1 Map are registered properly?"

    if mask_path is not None:
        mask_mri = load_mri(mask_path, bool)
        assert np.allclose(
            mask_mri.affine, T10_mri.affine
        ), "Affine transformations differ, are you sure the mask and T1 Map are registered properly?"
        mask = mask_mri.data
        T1_mri *= mask
        T10_mri *= mask
    else:
        mask = (T10_mri.data > 1e-10) * (T1_mri.data > 1e-10)
        T1_mri.data[~mask] = np.nan
        T10_mri.data[~mask] = np.nan

    concentrations = concentration_from_T1(T1=T1_mri.data, T1_0=T10_mri.data, r1=r1)
    save_mri(SimpleMRI(concentrations, T10_mri.affine), output_path)


if __name__ == "__main__":
    import typer

    typer.run(main)
