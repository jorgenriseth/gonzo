import json
from pathlib import Path

import nibabel
import numpy as np
import scipy
from loguru import logger
from numpy.lib.stride_tricks import sliding_window_view

from gonzo.utils import create_csf_mask


def T1_lookup_table(
    TRse: float, TI: float, TE: float, T1_low: float, T1_hi: float
) -> tuple[np.ndarray, np.ndarray]:
    T1_grid = np.arange(T1_low, T1_hi + 1)
    TR = TRse - 2 * TE
    Sse = 1 - np.exp(-TR / T1_grid)
    Sir = 1 - (1 + Sse) * np.exp(-TI / T1_grid)
    fractionCurve = Sir / Sse
    return fractionCurve, T1_grid


def estimate_T1_mixed(
    IR_nii_path: Path,
    SE_nii_path: Path,
    meta_path: Path,
    T1_low: float,
    T1_hi: float,
) -> nibabel.nifti1.Nifti1Image:
    SE_nii = nibabel.nifti1.load(SE_nii_path)
    IR_nii = nibabel.nifti1.load(IR_nii_path)
    with open(meta_path, "r") as f:
        meta = json.load(f)

    IR = IR_nii.get_fdata(dtype=np.single)
    SE = SE_nii.get_fdata(dtype=np.single)

    nonzero_mask = SE != 0
    F_data = np.nan * np.zeros_like(IR)
    F_data[nonzero_mask] = IR[nonzero_mask] / SE[nonzero_mask]

    TR_se, TI, TE = meta["TR_SE"], meta["TI"], meta["TE"]
    F, T1_grid = T1_lookup_table(TR_se, TI, TE, T1_low, T1_hi)
    interpolator = scipy.interpolate.interp1d(
        F, T1_grid, kind="nearest", bounds_error=False, fill_value=np.nan
    )
    T1_volume = interpolator(F_data).astype(np.single)
    nii = nibabel.nifti1.Nifti1Image(T1_volume, IR_nii.affine)
    nii.set_sform(nii.affine, "scanner")
    nii.set_qform(nii.affine, "scanner")
    return nii


def mixed_mask(SE_nii_path: Path, quantile: float) -> nibabel.nifti1.Nifti1Image:
    SE_nii = nibabel.nifti1.load(SE_nii_path)
    SE = SE_nii.get_fdata(dtype=np.single)
    mask = SE > np.quantile(SE, quantile)
    nii = nibabel.nifti1.Nifti1Image(mask.astype(np.single), SE_nii.affine)
    nii.set_sform(nii.affine, "scanner")
    nii.set_qform(nii.affine, "scanner")
    return nii


def filtering(vol):
    v = sliding_window_view(vol, (11, 11))
    m = np.nanmedian(v, axis=(-2, -1))
    s = np.nanstd(v, axis=(-2, -1))
    med = np.zeros_like(vol)
    med[5:-5, 5:-5] = m

    stand = np.zeros_like(vol)
    stand[5:-5, 5:-5] = s

    filter = (vol - med) / stand > 3
    return filter


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--SE", type=Path, required=True)
    parser.add_argument("--IR", type=Path, required=True)
    parser.add_argument("--meta", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--postprocessed", type=Path)
    args = parser.parse_args()

    # Create T1-maps
    T1map_nii = estimate_T1_mixed(args.IR, args.SE, args.meta, T1_low=1, T1_hi=10000)
    logger.info(f"Storing T1map as {args.output}")
    nibabel.nifti1.save(T1map_nii, args.output)

    if args.postprocessed is not None:
        SE = nibabel.nifti1.load(args.SE).get_fdata(dtype=np.single)
        mask = create_csf_mask(SE, use_li=True)
        masked_T1map = T1map_nii.get_fdata(dtype=np.single)
        masked_T1map[~mask] = np.nan
        masked_T1map_nii = nibabel.nifti1.Nifti1Image(
            masked_T1map, T1map_nii.affine, T1map_nii.header
        )
        nibabel.nifti1.save(masked_T1map_nii, args.postprocessed)
