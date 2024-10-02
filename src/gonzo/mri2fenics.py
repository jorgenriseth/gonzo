import argparse
import functools
from pathlib import Path
from typing import Callable, Optional

import dolfin as df
import nibabel
import numpy as np
from pantarei import FenicsStorage, hdf2fenics

from gonzo.utils import apply_affine, nan_filter_gaussian


def mri2fem_interpolate(
    D: np.ndarray,
    affine: np.ndarray,
    V: df.FunctionSpace,
    datafilter: Optional[Callable[[np.ndarray], np.ndarray]] = None,
) -> df.Function:
    if datafilter is not None:
        D = datafilter(D)
    u = df.Function(V)
    z = V.tabulate_dof_coordinates()
    ind = np.rint(apply_affine(np.linalg.inv(affine), z)).astype(int)
    i, j, k = ind.T
    u.vector()[:] = D[i, j, k]
    return u


def smooth_extension(D: np.ndarray, sigma: float, truncate: float = 4) -> np.ndarray:
    return np.where(np.isnan(D), nan_filter_gaussian(D, sigma, truncate), D)


def read_image(
    filename: Path,
    functionspace: df.FunctionSpace,
    datafilter: Optional[Callable[[np.ndarray], np.ndarray]] = None,
) -> df.Function:
    mri_volume = nibabel.nifti1.load(filename)
    voxeldata = mri_volume.get_fdata(dtype=np.single)
    return mri2fem_interpolate(voxeldata, mri_volume.affine, functionspace, datafilter)


def fenicsstorage2xdmf(
    filepath, funcname: str, subnames: str | list[str], outputdir: Path
) -> None:
    file = FenicsStorage(filepath, "r")
    file.to_xdmf(funcname, subnames, outputdir)
    file.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--mris", nargs="+", type=Path, required=True)
    parser.add_argument("--mesh_hdf", type=Path, required=True)
    parser.add_argument("--timestamps_txt", type=Path, required=True)
    parser.add_argument("--output_hdf", type=Path, required=True)
    parser.add_argument("--femfamily", type=str, default="CG")
    parser.add_argument("--femdegree", type=int, default=1)
    args = parser.parse_args()

    domain = hdf2fenics(args.mesh_hdf, pack=True)
    V = df.FunctionSpace(domain, args.femfamily, args.femdegree)
    concentration_data = sorted(args.mris)
    timestamps = np.loadtxt(args.timestamps_txt)

    assert len(concentration_data) > 0
    assert len(timestamps) == len(concentration_data)

    datafilter = functools.partial(smooth_extension, sigma=0.5, truncate=6)

    outfile = FenicsStorage(str(args.output_hdf), "w")
    outfile.write_domain(domain)
    for ti, ci in zip(timestamps, concentration_data):
        mri_volume = nibabel.nifti1.load(ci)
        voxeldata = mri_volume.get_fdata(dtype=np.single)
        c_data_fenics = mri2fem_interpolate(
            voxeldata, mri_volume.affine, V, datafilter=datafilter
        )
        outfile.write_checkpoint(c_data_fenics, name="total_concentration", t=ti)
    outfile.close()

    fenicsstorage2xdmf(
        outfile.filepath,
        "total_concentration",
        "total_concentration",
        lambda _: outfile.filepath.parent / "visual/data.xdmf",
    )
