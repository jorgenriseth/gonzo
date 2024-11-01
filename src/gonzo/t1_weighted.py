import click
from pathlib import Path

import numpy as np
import simple_mri as sm


@click.command()
@click.option("--input", type=Path, required=True)
@click.option("--reference", type=Path, required=True)
@click.option("--mask", type=Path, required=True)
@click.option("--output", type=Path, required=True)
def T1w_sigdiff(input: Path, reference: Path, mask: Path, output: Path):
    vol_mri = sm.load_mri(input, dtype=np.single)
    ref_mri = sm.load_mri(reference, dtype=np.single)
    vol = vol_mri.data
    ref = ref_mri.data

    mask_mri = sm.load_mri(mask, dtype=bool)
    mask = mask_mri.data * (ref > 0)

    signal_diff = np.nan * np.zeros_like(vol)
    signal_diff[mask] = vol[mask] / ref[mask] - 1
    signal_diff_mri = sm.SimpleMRI(signal_diff, affine=vol_mri.affine)
    sm.save_mri(signal_diff_mri, output, np.single)


def normalize_image(input: Path, refroi: Path, output: Path) -> Path:
    image = sm.load_mri(input, dtype=np.single)
    refroi = sm.load_mri(refroi, dtype=bool)
    sm.assert_same_space(image, refroi)
    normalized_data = image.data / np.median(image.data[refroi.data])
    normalized_mri = sm.SimpleMRI(normalized_data, image.affine)
    sm.save_mri(normalized_mri, output, dtype=np.single)
    return output


@click.command()
@click.option("--input", type=Path, required=True)
@click.option("--refroi", type=Path, required=True)
@click.option("--output", type=Path, required=True)
def T1w_normalize(**kwargs):
    normalize_image(**kwargs)
