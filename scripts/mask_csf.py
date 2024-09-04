from pathlib import Path

import numpy as np

from gonzo.utils import create_csf_mask
from gonzo.simple_mri import load_mri, save_mri, SimpleMRI


def main(input: Path, output: Path, connectivity: int = 2, li: bool = False):
    mri = load_mri(input, np.single)
    mask = create_csf_mask(mri.data, connectivity, li)
    assert np.max(mask) > 0
    save_mri(SimpleMRI(mask, mri.affine), output, np.uint8)


if __name__ == "__main__":
    import typer

    typer.run(main)
