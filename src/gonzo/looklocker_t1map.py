import click
import warnings
from functools import partial
from pathlib import Path
from typing import Optional

import numpy as np
import scipy
import skimage
import tqdm
from scipy.optimize import OptimizeWarning

from gonzo.utils import nan_filter_gaussian, mri_facemask
from simple_mri import SimpleMRI, load_mri, save_mri

T1_ROOF = 10000


def f(t, x1, x2, x3):
    return np.abs(x1 * (1.0 - (1 + x2**2) * np.exp(-(x3**2) * t)))


@np.errstate(divide="raise", invalid="raise", over="raise")
def curve_fit_wrapper(f, t, y, p0):
    """Raises error instead of catching numpy warnings, such that
    these cases may be treated."""
    with warnings.catch_warnings():
        warnings.simplefilter("error", OptimizeWarning)
        popt, _ = scipy.optimize.curve_fit(f, xdata=t, ydata=y, p0=p0, maxfev=1000)
    return popt


def fit_voxel(time_s: np.ndarray, pbar, m: np.ndarray) -> np.ndarray:
    if pbar is not None:
        pbar.update(1)
    x1 = 1.0
    x2 = np.sqrt(1.25)
    T1 = time_s[np.argmin(m)] / np.log(1 + x2**2)
    x3 = np.sqrt(1 / T1)
    p0 = np.array((x1, x2, x3))
    if not np.all(np.isfinite(m)):
        return np.nan * np.zeros_like(p0)
    try:
        popt = curve_fit_wrapper(f, time_s, m, p0)
    except (OptimizeWarning, FloatingPointError):
        return np.nan * np.zeros_like(p0)
    except RuntimeError as e:
        if "maxfev" in str(e):
            return np.nan * np.zeros_like(p0)
        raise e
    return popt


def estimate_t1map(t_data: np.ndarray, D: np.ndarray, affine: np.ndarray) -> SimpleMRI:
    mask = mri_facemask(D[..., 0])
    valid_voxels = (np.nanmax(D, axis=-1) > 0) * mask

    D_normalized = np.nan * np.zeros_like(D)
    D_normalized[valid_voxels] = (
        D[valid_voxels] / np.nanmax(D, axis=-1)[valid_voxels, np.newaxis]
    )
    voxel_mask = np.array(np.where(valid_voxels)).T
    Dmasked = np.array([D_normalized[i, j, k] for (i, j, k) in voxel_mask])

    with tqdm.tqdm(total=len(Dmasked)) as pbar:
        voxel_fitter = partial(fit_voxel, t_data, pbar)
        vfunc = np.vectorize(voxel_fitter, signature="(n) -> (3)")
        fitted_coefficients = vfunc(Dmasked)

    x1, x2, x3 = (
        fitted_coefficients[:, 0],
        fitted_coefficients[:, 1],
        fitted_coefficients[:, 2],
    )

    I, J, K = voxel_mask.T
    T1map = np.nan * np.zeros_like(D[..., 0])
    T1map[I, J, K] = (x2 / x3) ** 2 * 1000.0  # convert to ms
    T1map = np.minimum(T1map, T1_ROOF)
    return SimpleMRI(T1map.astype(np.single), affine)


def postprocess_T1map(
    T1map_mri: SimpleMRI,
    T1_lo: float,
    T1_hi: float,
    radius: int = 10,
    erode_dilate_factor: float = 1.3,
    mask: Optional[np.ndarray] = None,
) -> SimpleMRI:
    T1map = T1map_mri.data.copy()
    if mask is None:
        # Create mask for largest island.
        mask = skimage.measure.label(np.isfinite(T1map))
        regions = skimage.measure.regionprops(mask)
        regions.sort(key=lambda x: x.num_pixels, reverse=True)
        mask = mask == regions[0].label
        skimage.morphology.remove_small_holes(
            mask, 10 ** (mask.ndim), connectivity=2, out=mask
        )
        skimage.morphology.binary_dilation(
            mask, skimage.morphology.ball(radius), out=mask
        )
        skimage.morphology.binary_erosion(
            mask, skimage.morphology.ball(erode_dilate_factor * radius), out=mask
        )

    # Remove non-zero artifacts outside of the mask.
    surface_vox = np.isfinite(T1map) * (~mask)
    print(f"Removing {surface_vox.sum()} voxels outside of the head mask")
    T1map[~mask] = np.nan

    # Remove outliers within the mask.
    outliers = np.logical_or(T1map < T1_lo, T1_hi < T1map)
    print("Removing", outliers.sum(), f"voxels outside the range ({T1_lo}, {T1_hi}).")
    T1map[outliers] = np.nan
    if np.isfinite(T1map).sum() / T1map.size < 0.01:
        raise RuntimeError(
            "After outlier removal, less than 1% of the image is left. Check image units."
        )

    # Fill internallly missing values
    fill_mask = np.isnan(T1map) * mask
    while fill_mask.sum() > 0:
        print(f"Filling in {fill_mask.sum()} voxels within the mask.")
        T1map[fill_mask] = nan_filter_gaussian(T1map, 1.0)[fill_mask]
        fill_mask = np.isnan(T1map) * mask
    return SimpleMRI(T1map, T1map_mri.affine)


@click.command()
@click.option("--input", type=Path, required=True)
@click.option("--timestamps", type=Path, required=True)
@click.option("--output", type=Path, required=True)
@click.option("--T1_low", type=float, default=1)
@click.option("--T1_high", type=float, default=float("Inf"))
@click.option("--postprocessed", type=Path)
@click.option("--R1", type=Path)
@click.option("--R1_postprocessed", type=Path)
def looklocker_t1map(
    input,
    timestamps,
    output,
):
    time = np.loadtxt(timestamps) / 1000
    LL_mri = load_mri(input, dtype=np.single)
    T1map_mri = estimate_t1map(time, LL_mri.data, LL_mri.affine)
    output.parent.mkdir(exist_ok=True, parents=True)
    save_mri(T1map_mri, output, dtype=np.single)


if __name__ == "__main__":
    looklocker_t1map()
