from pathlib import Path
from typing import Optional

import click
import dolfin as df
import numpy as np
import scipy
import pandas as pd
import tqdm
import pantarei as pr
from pantarei import FenicsStorage, fenicsstorage2xdmf

from gonzo.utils import apply_affine, nan_filter_gaussian
from simple_mri import load_mri, SimpleMRI


def extract_sequence_timestamps(
    timetable_path: Path, subject: str, sequence_label: str
):
    try:
        timetable = pd.read_csv(timetable_path, sep="\t")
    except pd.errors.EmptyDataError:
        raise RuntimeError(f"Timetable-file {timetable_path} is empty.")
    subject_sequence_entries = (timetable["subject"] == subject) & (
        timetable["sequence_label"] == sequence_label
    )
    try:
        acq_times = timetable[subject_sequence_entries][
            "acquisition_relative_injection"
        ]
    except ValueError as e:
        print(timetable)
        print(subject, sequence_label)
        print(subject_sequence_entries)
        raise e
    times = np.array(acq_times)
    assert len(times) > 0, f"Couldn't find time for {subject}: {sequence_label}"
    return times


def smooth_dilation(D: np.ndarray, sigma: float, truncate: float = 4) -> np.ndarray:
    return np.where(np.isfinite(D), D, nan_filter_gaussian(D, sigma, truncate))


def nearest_neighbour(
    D: np.ndarray, inds: np.ndarray, valid_indices: Optional[np.ndarray] = None
) -> np.ndarray:
    i, j, k = inds.T
    if valid_indices is None:
        I, J, K = np.array(np.where(np.isfinite(D)))
    else:
        I, J, K = valid_indices
    interp = scipy.interpolate.NearestNDInterpolator(np.array((I, J, K)).T, D[I, J, K])
    D_out = D.copy()
    D_out[i, j, k] = interp(i, j, k)
    num_nan_values = (~np.isfinite(D_out[i, j, k])).sum()
    assert num_nan_values == 0
    return D_out


def smooth_extension(D, inds, sigma, truncate, maxiter=10, fallback=True):
    i, j, k = inds.T
    num_nan_values = (~np.isfinite(D[i, j, k])).sum()
    for _ in range(maxiter):
        D = smooth_dilation(D, sigma, truncate)
        num_nan_values = (~np.isfinite(D[i, j, k])).sum()
        if num_nan_values == 0:
            return D

    if not fallback:
        raise RuntimeError(
            f"Couldn't extend data within {maxiter} iterations, missing {num_nan_values}"
        )
    return nearest_neighbour(D, inds)


def map_concentration(
    subject: str,
    concentration_paths: list[Path],
    meshpath: Path,
    csfmask_path: Path,
    timetable: Path,
    output: Path,
    femfamily: str,
    femdegree: int,
    visualdir: Optional[Path] = None,
):
    timestamps = np.maximum(
        0, extract_sequence_timestamps(timetable, subject, "looklocker")
    )
    domain = pr.hdf2fenics(meshpath, pack=True)
    V = df.FunctionSpace(domain, femfamily, femdegree)
    dof_coordinates = V.tabulate_dof_coordinates()
    boundary_dofs = np.array(
        [
            dof
            for dof in df.DirichletBC(V, df.Constant(0), "on_boundary")
            .get_boundary_values()
            .keys()
        ]
    )
    mask_mri = load_mri(csfmask_path, dtype=bool)
    mask = mask_mri.data
    concentration_mri = load_mri(concentration_paths[0], dtype=np.single)
    affine = concentration_mri.affine
    boundary_dof_coordinates = dof_coordinates[boundary_dofs]
    boundary_inds = np.rint(
        apply_affine(np.linalg.inv(affine), boundary_dof_coordinates)
    ).astype(int)
    i, j, k = boundary_inds.T

    inds = np.rint(apply_affine(np.linalg.inv(affine), dof_coordinates)).astype(int)
    I, J, K = inds.T

    assert len(concentration_paths) > 0
    assert len(timestamps) == len(concentration_paths)

    outfile = FenicsStorage(str(output), "w")
    outfile.write_domain(domain)
    for ti, ci in zip(tqdm.tqdm(timestamps), concentration_paths):
        concentration_mri = load_mri(ci, dtype=np.single)
        affine = concentration_mri.affine

        boundary_data = np.nan * np.zeros_like(concentration_mri.data)
        boundary_data[mask] = concentration_mri.data[mask]
        boundary_data = smooth_extension(
            boundary_data, boundary_inds, sigma=1, truncate=4, maxiter=3
        )

        u_boundary = df.Function(V)
        u_boundary.vector()[boundary_dofs] = boundary_data[i, j, k]
        outfile.write_checkpoint(u_boundary, name="boundary_concentration", t=ti)

        internal_data = np.nan * np.zeros_like(concentration_mri.data)
        internal_data[~mask] = concentration_mri.data[~mask]
        internal_data = smooth_extension(
            internal_data, inds, sigma=1, truncate=4, maxiter=3
        )

        u_internal = df.Function(V)
        u_internal.vector()[:] = internal_data[I, J, K]
        outfile.write_checkpoint(u_internal, name="concentration", t=ti)
    outfile.close()

    if visualdir is not None:
        fenicsstorage2xdmf(
            FenicsStorage(outfile.filepath, "r"),
            "concentration",
            "internal",
            lambda _: visualdir / "concentrations_internal.xdmf",
        )
        fenicsstorage2xdmf(
            FenicsStorage(outfile.filepath, "r"),
            "boundary_concentration",
            "boundary",
            lambda _: visualdir / "concentrations_boundary.xdmf",
        )


if __name__ == "__main__":
    import click
    import re

    @click.command()
    @click.argument("concentration_paths", type=Path, nargs=-1, required=True)
    @click.option("--meshpath", type=Path, required=True)
    @click.option("--csfmask_path", type=Path, required=True)
    @click.option("--timetable", type=Path, required=True)
    @click.option("--output", type=Path, required=True)
    @click.option("--femfamily", type=str, default="CG")
    @click.option("--femdegree", type=int, default=1)
    @click.option("--visualdir", type=Path)
    def main(concentration_paths, **kwargs):
        subject_re = re.compile(r"(?P<subject>sub-(control|patient)*\d{2})")
        m = subject_re.search(str(concentration_paths[0]))
        if m is None:
            raise ValueError(f"Couldn't find subject in path {concentration_paths[0]}")
        map_concentration(m.groupdict()["subject"], concentration_paths, **kwargs)

    main()
