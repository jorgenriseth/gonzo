from pathlib import Path
import click

import meshio
import numpy as np
import pyvista as pv
import pandas as pd
import dolfin as df
import pantarei as pr

from pathlib import Path


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
    return np.maximum(0.0, times)


def cell_matrix_to_vtk_cells(cells: np.ndarray):
    num_points_stack = cells.shape[1] * np.ones((cells.shape[0], 1), dtype=cells.dtype)
    return np.concatenate((num_points_stack, cells), axis=1).ravel()


def convert_to_vtk(hdf_data: Path, output: Path):
    hdf = df.HDF5File(df.MPI.comm_world, str(hdf_data), "r")
    domain = pr.read_domain(hdf)
    concentration_times = pr.read_timevector(hdf, "concentration")
    boundary_times = pr.read_timevector(hdf, "boundary_concentration")
    concentrations = [
        pr.read_function(hdf, "concentration", domain, idx) for idx in range(5)
    ]
    boundary_concentrations = [
        pr.read_function(hdf, "boundary_concentration", domain, idx) for idx in range(5)
    ]
    dti = pr.read_function(hdf, "DTI", domain)
    md = pr.read_function(hdf, "MD", domain)
    fa = pr.read_function(hdf, "FA", domain)

    parcellations = df.MeshFunction("size_t", domain, 3)
    hdf.read(parcellations, "parcellations")
    pr.close(hdf)

    cells = cell_matrix_to_vtk_cells(domain.cells())
    celltypes = [pv.CellType.TETRA] * len(domain.cells())
    points = domain.coordinates()
    grid = pv.UnstructuredGrid(cells, celltypes, points)

    grid.cell_data["subdomains"] = domain.subdomains.array()
    grid.cell_data["parcellations"] = parcellations.array()
    for idx, (ci, cb_i) in enumerate(zip(concentrations, boundary_concentrations)):
        grid.point_data[f"concentration-{int(concentration_times[idx])}"] = (
            ci.compute_vertex_values()
        )
        grid.point_data[f"boundary-concentration-{int(boundary_times[idx])}"] = (
            cb_i.compute_vertex_values()
        )

    for name, func in [("dt", dti), ("fa", fa), ("md", md)]:
        output_vec = func.vector()[:]
        output_dim = output_vec.shape[0] // domain.cells().shape[0]
        grid.cell_data[name] = output_vec.reshape(-1, output_dim).squeeze()
    pv.save_meshio(output, grid)


@click.command()
@click.option("--input", "hdf_data", type=Path, required=True)
@click.option("--output", "output", type=Path, required=True)
def main(**kwargs):
    convert_to_vtk(**kwargs)


if __name__ == "__main__":
    main()
