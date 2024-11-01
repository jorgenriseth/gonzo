from pathlib import Path

import click
import numpy as np
import skimage
from simple_mri import load_mri, save_mri, SimpleMRI, assert_same_space

from gonzo.utils import create_csf_mask
from gonzo.utils import largest_island


def intracranial_mask(csf_mask: SimpleMRI, segmentation: SimpleMRI):
    assert_same_space(csf_mask, segmentation)
    combined_mask = csf_mask.data + (segmentation.data != 0)
    island = largest_island(combined_mask, connectivity=1)
    hole_filled = skimage.morphology.binary_closing(island, skimage.morphology.ball(9))
    hole_filled = skimage.morphology.remove_small_holes(
        island, area_threshold=1024, connectivity=2
    )
    return SimpleMRI(data=hole_filled, affine=segmentation.affine)


@click.command()
@click.option("--csfmask", type=Path, required=True)
@click.option("--brain_seg", type=Path, required=True)
@click.option("--output", type=Path, required=True)
def mask_intracranial(csf_mask: Path, brain_mask: Path, output):
    csf = load_mri(csf_mask, dtype=bool)
    brain = load_mri(brain_mask, dtype=bool)
    intracranial_mask_mri = intracranial_mask(csf, brain)
    save_mri(intracranial_mask_mri, output, dtype=np.uint8)


@click.command()
@click.option("--input", type=Path, required=True)
@click.option("--output", type=Path, required=True)
@click.option("--connectivity", type=int, default=2)
@click.option("--li", type=bool, is_flag=True, default=False)
def mask_csf(input: Path, output: Path, connectivity: int = 2, li: bool = False):
    mri = load_mri(input, np.single)
    mask = create_csf_mask(mri.data, connectivity, li)
    assert np.max(mask) > 0
    save_mri(SimpleMRI(mask, mri.affine), output, np.uint8)
