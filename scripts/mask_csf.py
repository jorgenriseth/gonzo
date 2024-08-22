from pathlib import Path

import nibabel.nifti1 as nifti1
import numpy as np

from gonzo.utils import create_csf_mask


def main(input: Path, output: Path, connectivity: int = 2, li: bool = False):
    nii = nifti1.load(input)
    vol = nii.get_fdata(dtype=np.single)
    mask = create_csf_mask(vol, connectivity, li)
    mask_nii = nifti1.Nifti1Image(mask.astype(np.uint8), nii.affine)
    nifti1.save(mask_nii, output)


if __name__ == "__main__":
    import typer

    typer.run(main)
