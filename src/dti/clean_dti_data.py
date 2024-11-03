from pathlib import Path

import click
import numpy as np
import scipy

from simple_mri import SimpleMRI, load_mri, save_mri


def clean_dti_data(dti: Path, mask: Path, output: Path):
    dti_mri = load_mri(dti, dtype=np.single)
    dti_mri.data = extend_to_9_component_array(dti_mri.data)
    dti = dti_mri.data

    mask_mri = load_mri(mask, dtype=bool)
    mask = mask_mri.data

    D = dti.reshape(*dti.shape[:3], 3, 3)
    valid = is_valid_tensor(D)
    i, j, k = np.where(mask * ~valid)
    I, J, K = np.where(mask * valid)
    interpolated = np.nan * np.zeros_like(dti)
    interpolated[mask] = dti[mask]
    interpolated[i, j, k] = (
        scipy.interpolate.griddata(
            (I, J, K), dti[I, J, K], (i, j, k), method="nearest"
        ),
    )
    save_mri(
        SimpleMRI(
            reduce_to_6_component_array(interpolated.reshape(*dti.shape[:3], 1, 9)),
            dti_mri.affine,
        ),
        output,
        dtype=np.single,
    )


def extend_to_9_component_array(data: np.ndarray) -> np.ndarray:
    if data.shape[-1] == 9:
        return data
    elif data.shape[-1] == 6:
        newdata = np.zeros((*data.shape[:-1], 9), dtype=data.dtype)
        newdata[..., 0:3] = data[..., :3]
        newdata[..., 4:6] = data[..., 3:5]
        newdata[..., 8] = data[..., 5]
        newdata[..., 3] = data[..., 1]
        newdata[..., 6] = data[..., 2]
        newdata[..., 7] = data[..., 4]
        return newdata
    else:
        raise ValueError(f"Data has shape {data.shape}, should have last dim 6 or 9")


def reduce_to_6_component_array(data: np.ndarray) -> np.ndarray:
    if data.shape[-1] == 6:
        return data
    elif data.shape[-1] == 9:
        newdata = np.zeros((*data.shape[:-1], 6), dtype=data.dtype)
        newdata[..., :3] = data[..., :3]
        newdata[..., 3:5] = data[..., 4:6]
        newdata[..., 5] = data[..., 8]
        return newdata
    else:
        raise ValueError(f"Data has shape {data.shape}, should have last dim 6 or 9")


def is_valid_tensor(D: np.ndarray) -> np.ndarray:
    eigvals = np.linalg.eigvalsh(D)
    FA = fractional_anisotropy(eigvals)
    positives = (eigvals[..., 0] > 0) * (eigvals[..., 1] > 0) * (eigvals[..., 2] > 0)
    valid = positives * (FA < 1.0) * (FA > 0.0)
    return valid


def fractional_anisotropy(eigvals: np.ndarray) -> np.ndarray:
    MD = eigvals.sum(axis=-1) / 3.0
    mask = np.abs(MD) > 0
    FA = np.zeros_like(MD)
    FA[mask] = np.sqrt(
        1.5
        * np.sum((eigvals[mask] - MD[mask, np.newaxis]) ** 2, axis=-1)
        / np.sum(eigvals[mask] ** 2, axis=-1)
    )
    return FA


@click.command()
@click.option("--dti", type=Path, required=True)
@click.option("--mask", type=Path, required=True)
@click.option("--output", type=Path, required=True)
def clean(**kwargs):
    clean_dti_data(**kwargs)


if __name__ == "__main__":
    clean()
