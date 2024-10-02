from pathlib import Path

import nibabel
import numpy as np


def normalize_image(image_path: Path, refroi_path: Path, outputpath: Path) -> Path:
    image = nibabel.nifti1.load(image_path)
    refroi = nibabel.nifti1.load(refroi_path)

    assert np.allclose(
        refroi.affine, image.affine
    ), "Poor match between reference and image-transform."
    image_data = image.get_fdata(dtype=np.single)
    ref_mask = refroi.get_fdata().astype(bool)

    normalized_image_data = image_data / np.median(image_data[ref_mask])
    normalized_image = nibabel.nifti1.Nifti1Image(normalized_image_data, image.affine)
    nibabel.nifti1.save(normalized_image, outputpath)
    return outputpath


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--refroi", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    normalize_image(args.image, args.refroi, args.output)
