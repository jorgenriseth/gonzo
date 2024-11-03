from pathlib import Path

from typing import Optional
import click
import numpy as np

from simple_mri import load_mri, save_mri, SimpleMRI, assert_same_space


def concentration_from_T1(T1: np.ndarray, T1_0: np.ndarray, r1: float) -> np.ndarray:
    C = 1 / r1 * (1 / T1 - 1 / T1_0)
    return C


def concentration_from_R1(R1: np.ndarray, R1_0: np.ndarray, r1: float) -> np.ndarray:
    C = 1 / r1 * (R1 - R1_0)
    return C


@click.command()
@click.option("--input", type=Path, required=True)
@click.option("--reference", type=Path, required=True)
@click.option("--output", type=Path, required=True)
@click.option("--r1", type=float, required=True)
@click.option("--mask", type=Path)
def concentration(
    input: Path,
    reference: Path,
    output: Path,
    r1: float,
    mask: Optional[Path] = None,
):
    T1_mri = load_mri(input, np.single)
    T10_mri = load_mri(reference, np.single)
    assert_same_space(T1_mri, T10_mri)

    if mask is not None:
        mask_mri = load_mri(mask, bool)
        assert_same_space(mask_mri, T10_mri)
        mask_data = mask_mri.data * (T10_mri.data > 1e-10) * (T1_mri.data > 1e-10)
        T1_mri.data *= mask_data
        T10_mri.data *= mask_data
    else:
        mask_data = (T10_mri.data > 1e-10) * (T1_mri.data > 1e-10)
        T1_mri.data[~mask_data] = np.nan
        T10_mri.data[~mask_data] = np.nan

    concentrations = np.nan * np.zeros_like(T10_mri.data)
    concentrations[mask_data] = concentration_from_T1(
        T1=T1_mri.data[mask_data], T1_0=T10_mri.data[mask_data], r1=r1
    )
    save_mri(SimpleMRI(concentrations, T10_mri.affine), output, np.single)


if __name__ == "__main__":
    concentration()
