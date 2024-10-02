from pathlib import Path
import nibabel
import numpy as np


import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--reference", type=Path, required=True)
parser.add_argument("--image", type=Path, required=True)
parser.add_argument("--mask", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()

ref_nii = nibabel.nifti1.load(args.reference)
ref = ref_nii.get_fdata(dtype=np.single)
vol_nii = nibabel.nifti1.load(args.image)
vol = vol_nii.get_fdata(dtype=np.single)

brainmask_nii = nibabel.nifti1.load(args.mask)
brainmask = brainmask_nii.get_fdata().astype(bool) * (ref > 0)
signal_diff = np.nan * np.zeros_like(vol)
signal_diff[brainmask] = vol[brainmask] / ref[brainmask] - 1
signal_diff_nii = nibabel.nifti1.Nifti1Image(
    signal_diff, affine=vol_nii.affine, header=vol_nii.header
)
nibabel.nifti1.save(signal_diff_nii, args.output)
