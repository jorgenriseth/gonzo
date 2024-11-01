from pathlib import Path

import click
import nibabel.nifti1 as nifti1


def T1_hybridization(
    ll_path: Path, mixed_path: Path, csf_mask_path: Path, mixed_threshold: float = 1500
) -> nifti1.Nifti1Image:
    mixed_mri = nifti1.load(mixed_path)
    mixed = mixed_mri.get_fdata()

    ll_mri = nifti1.load(ll_path)
    ll = ll_mri.get_fdata()

    csf_mask_mri = nifti1.load(csf_mask_path)
    csf_mask = csf_mask_mri.get_fdata().astype(bool)

    hybrid = ll
    newmask = csf_mask * (ll > mixed_threshold)
    hybrid[newmask] = mixed[newmask]
    return nifti1.Nifti1Image(hybrid, affine=ll_mri.affine, header=ll_mri.header)


@click.command()
@click.option("--csfmask", type=Path, required=True)
@click.option("--ll", type=Path, required=True)
@click.option("--mixed", type=Path, required=True)
@click.option("--output", type=Path, required=True)
def hybrid_t1map(csfmask, ll, mixed, output):
    hybrid = T1_hybridization(ll, mixed, csfmask, mixed_threshold=1500)
    nifti1.save(hybrid, output)


if __name__ == "__main__":
    hybrid_t1map()
