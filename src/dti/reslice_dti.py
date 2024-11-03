import subprocess
import tempfile
from pathlib import Path
from typing import Optional

import click
import numpy as np
import matplotlib.pyplot as plt

from simple_mri import load_mri, SimpleMRI, save_mri


def construct_tensor_from_eigs(dti_folder: Path, prefix_pattern: str) -> SimpleMRI:
    eigvec = load_mri(dti_folder / f"{prefix_pattern}_V1.nii.gz", np.single)
    spatial_shape = eigvec.data.shape[:3]
    B = np.zeros((*spatial_shape, 3, 3), dtype=eigvec.data.dtype)
    L = np.zeros_like(B)
    for i in range(1, 4):
        eigvec = load_mri(dti_folder / f"{prefix_pattern}_V{i}.nii.gz", np.single)
        eigval = load_mri(dti_folder / f"{prefix_pattern}_L{i}.nii.gz", np.single)
        B[..., :, i - 1] = eigvec.data
        L[..., i - 1, i - 1] = eigval.data
    valid_mask = np.linalg.det(L) != 0
    Binv = np.zeros_like(B)
    Binv[valid_mask] = np.linalg.inv(B[valid_mask])
    return SimpleMRI(B @ L @ Binv, eigvec.affine)


def construct_tensor_from_vector_array(tensor: SimpleMRI) -> SimpleMRI:
    spatial_shape = tensor.data.shape[:3]
    Dt = np.zeros((*spatial_shape, 3, 3), dtype=tensor.data.dtype)
    if tensor.data.shape[-1] == 6:
        Dt[..., 0, :] = Dt[..., :, 0] = tensor.data[..., :3]
        Dt[..., 1, 1:] = Dt[..., 1:, 1] = tensor.data[..., 3:5]
        Dt[..., 2, 2] = tensor.data[..., 5]
    elif tensor.data.shape[-1] == 9:
        Dt[...] = tensor.data.reshape(*spatial_shape, 3, 3).copy()
    return SimpleMRI(Dt, tensor.affine)


@click.command()
@click.option("-input_folder", type=Path, required=True)
@click.option("-prefix_pattern", type=Path, required=True)
@click.option("-output", type=Path, required=True)
@click.option("--from_tensor", default=False)
def construct_and_save_tensor(
    input_folder: Path, prefix_pattern: str, output: Path, from_tensor: bool
):
    if from_tensor:
        tensor_in = load_mri(
            input_folder / f"{prefix_pattern}_tensor.nii.gz", dtype=np.single
        )
        tensor_out = construct_tensor_from_vector_array(tensor_in)
    else:
        tensor_out = construct_tensor_from_eigs(input_folder, prefix_pattern)
    save_mri(tensor_out, output, dtype=tensor_out.data.dtype)


def reslice_4d(
    inpath: Path,
    fixed: Path,
    outpath: Path,
    transform: Optional[Path] = None,
    threads: int = 1,
) -> Path:
    if transform is None:
        transform = Path("")
    nframes = int(
        subprocess.check_output(
            f"mri_info --nframes {inpath} | grep -v INFO", shell=True
        )
    )
    with tempfile.TemporaryDirectory(prefix=outpath.stem) as tmpdir:
        tmppath = Path(tmpdir)
        for i in range(nframes):
            tmp_split = tmppath / f"slice{i}.nii.gz"
            tmp_reslice = tmppath / f"reslice{i}.nii.gz"
            subprocess.run(
                f"fslroi {inpath} {tmp_split} {i} 1", shell=True
            ).check_returncode()
            subprocess.run(
                f"greedy -d 3 -rf {fixed} -rm {tmp_split} {tmp_reslice} -r {transform} -threads {threads}",
                shell=True,
            ).check_returncode()
        components = [str(tmppath / f"reslice{i}.nii.gz") for i in range(nframes)]
        subprocess.run(
            f"fslmerge -t {outpath} {' '.join(components)}", shell=True
        ).check_returncode()
    return outpath


@click.command()
@click.option("--fixed", type=Path, required=True)
@click.option("--dtidir", type=Path, required=True)
@click.option("--prefix_pattern", type=str, required=True)
@click.option("--outdir", type=Path)
@click.option("--transform", type=Path)
@click.option("--threads", type=int, default=1)
def reslice_dti(
    fixed: Path,
    dtidir: Path,
    prefix_pattern: str,
    outdir: Path,
    transform: Path,
    threads: int,
    out_pattern: Optional[str] = None,
):
    if out_pattern is None:
        out_pattern = prefix_pattern

    for c in ["FA", "MD", *[f"L{i}" for i in range(1, 4)]]:
        inpath = dtidir / f"{prefix_pattern}_{c}.nii.gz"
        outpath = outdir / f"{out_pattern}_{c}.nii.gz"
        print(inpath, outpath)
        reslice_4d(inpath, fixed, outpath, transform, threads)

    with tempfile.TemporaryDirectory(prefix=out_pattern) as tmpdir:
        tmppath = Path(tmpdir)
        for Vi in [f"V{i}" for i in range(1, 4)]:
            inpath = dtidir / f"{prefix_pattern}_{Vi}.nii.gz"
            resliced = tmppath / f"{out_pattern}_{Vi}.nii.gz"
            outpath = outdir / resliced.name
            reslice_4d(inpath, fixed, resliced, transform, threads)
            resliced_mri = load_mri(resliced, dtype=np.single)
            norms = np.linalg.norm(resliced_mri.data, axis=-1, ord=2)
            resliced_mri.data[norms > 0] /= norms[norms > 0, np.newaxis]
            save_mri(resliced_mri, outpath, dtype=np.single)

    resliced_tensor = construct_tensor_from_eigs(outdir, out_pattern)
    save_mri(resliced_tensor, outdir / f"{out_pattern}_tensor.nii.gz", dtype=np.single)h


@click.command("eddy-index")
@click.option("--input", type=Path, required=True)
@click.option("--output", type=Path, required=True)
def create_eddy_index_file(input: Path, output: Path):
    nframes = int(
        subprocess.check_output(
            f"mri_info --nframes {inpath} | grep -v INFO", shell=True
        )
    )
    index = ["1"] * nframes
    with open(output, "w") as f:
        f.write(" ".join(index))
    
    


if __name__ == "__main__":
    reslice_dti()
