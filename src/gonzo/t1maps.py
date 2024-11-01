from pathlib import Path
from typing import Optional

import click
import numpy as np
import skimage
from simple_mri import SimpleMRI, load_mri, save_mri
from gonzo.utils import mri_facemask, nan_filter_gaussian


def convert_T1_to_R1(
    T1map_mri: SimpleMRI,
    scale: float = 1000,
    t1_low: float = 1,
    t1_high: float = float("inf"),
) -> SimpleMRI:
    valid_t1 = (t1_low <= T1map_mri.data) * (T1map_mri.data <= t1_high)
    R1map = np.nan * np.zeros_like(T1map_mri.data)
    R1map[valid_t1] = scale / np.minimum(
        t1_high, np.maximum(t1_low, T1map_mri.data[valid_t1])
    )
    R1map_mri = SimpleMRI(
        R1map,
        T1map_mri.affine,
    )
    return R1map_mri


@click.command()
@click.option("--input", type=Path, required=True)
@click.option("--output", type=Path, required=True)
@click.option("--scale", type=float, default=1000)
@click.option("--T1_low", type=float, default=1)
@click.option("--T1_high", type=float, default=float("Inf"))
def T1_to_R1(
    input: Path,
    output: Path,
    scale: float,
    t1_low: float,
    t1_high: float,
):
    T1map_mri = load_mri(input, dtype=np.single)
    R1map_mri = convert_T1_to_R1(T1map_mri, scale, t1_low, t1_high)
    save_mri(R1map_mri, output, dtype=np.single)


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
@click.option("--LL", type=Path, required=True, help="LookLocker image path")
@click.option("--T1map", type=Path, required=True, help="Raw T1-estimate")
@click.option("--output", type=Path, required=True)
@click.option("--T1_low", type=float, default=1)
@click.option("--T1_high", type=float, default=float("Inf"))
def looklocker_t1_postprocessing(
    ll: Path, t1map: Path, output: Path, t1_low: float, t1_high: float
):
    LL_mri = load_mri(ll, dtype=np.single)
    T1map_mri = load_mri(t1map, dtype=np.single)
    mask = mri_facemask(LL_mri.data[..., 0])
    postprocessed_mri = postprocess_T1map(
        T1map_mri,
        t1_low,
        t1_high,
        mask=mask,
    )
    save_mri(postprocessed_mri, output, dtype=np.single)
