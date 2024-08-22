import re
import warnings
from functools import partial
from pathlib import Path
from typing import Callable, Any, Optional

import nibabel
import numpy as np
import scipy
import skimage
import tqdm
from scipy.optimize import OptimizeWarning

from gonzo.utils import nan_filter_gaussian, mri_facemask
from gonzo.simple_mri import load_mri


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


def estimate_t1map(
    t_data: np.ndarray, D: np.ndarray, affine: np.ndarray
) -> nibabel.nifti1.Nifti1Image:
    mask = mri_facemask(D[0])
    valid_voxels = (np.nanmax(D, axis=0) > 0) * mask

    D_normalized = np.nan * np.zeros_like(D)
    D_normalized[:, valid_voxels] = (
        D[:, valid_voxels] / np.nanmax(D, axis=0)[valid_voxels]
    )
    voxel_mask = np.array(np.where(valid_voxels)).T
    Dmasked = np.array([D_normalized[:, i, j, k] for (i, j, k) in voxel_mask])

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
    T1map = np.nan * np.zeros_like(D[0])
    T1map[I, J, K] = (x2 / x3) ** 2 * 1000.0  # convert to ms
    return nibabel.nifti1.Nifti1Image(T1map.astype(np.single), affine)


def postprocess_T1map(
    T1map_mri: nibabel.nifti1.Nifti1Image,
    T1_lo: float,
    T1_hi: float,
    radius: int = 10,
    erode_dilate_factor: float = 1.3,
    mask: Optional[np.ndarray] = None,
) -> nibabel.nifti1.Nifti1Image:
    T1map = T1map_mri.get_fdata(dtype=np.single)

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
    return nibabel.nifti1.Nifti1Image(T1map, T1map_mri.affine)


def T1_to_R1(T1map_mri: nibabel.nifti1.Nifti1Image, scale: float = 1000):
    T1map = T1map_mri.get_fdata(dtype=np.single)
    return nibabel.nifti1.Nifti1Image(scale / T1map, T1map_mri.affine)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--timestamps", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--T1_low", type=int, default=150)
    parser.add_argument("--T1_hi", type=int, default=5500)
    parser.add_argument("--postprocessed", type=Path)
    parser.add_argument("--R1", type=Path)
    parser.add_argument("--R1_postprocessed", type=Path)
    args = parser.parse_args()

    LL_nii = nibabel.nifti1.load(args.input)
    mri = load_mri(args.input, np.single)
    time = np.loadtxt(args.timestamps) / 1000
    D = mri.data.transpose(3, 0, 1, 2)
    T1map_nii = estimate_t1map(time, D, mri.affine)

    args.output.parent.mkdir(exist_ok=True, parents=True)
    nibabel.nifti1.save(T1map_nii, args.output)

    if args.R1 is not None:
        R1 = T1_to_R1(T1map_nii)
        nibabel.nifti1.save(R1, args.R1)

    if args.postprocessed is not None:
        mask = mri_facemask(D[0])
        postprocessed = postprocess_T1map(
            T1map_nii,
            args.T1_low,
            args.T1_hi,
            mask=mask,
        )
        nibabel.nifti1.save(postprocessed, args.postprocessed)
        if args.R1_postprocessed is not None:
            R1_post = T1_to_R1(postprocessed)
            nibabel.nifti1.save(R1_post, args.R1_postprocessed)
