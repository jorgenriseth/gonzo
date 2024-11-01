from pathlib import Path

import click
import pyvista as pv
import nibabel as nibabel
import numpy as np
import simple_mri as sm


def mri_data_to_ndarray(
    grid: pv.StructuredGrid, data_name: str, shape: tuple[int, ...], mask: bool = True
) -> np.ndarray:
    data_array = grid.point_data[data_name]
    if mask:
        mask_array = grid.point_data["vtkValidPointMask"].astype(bool)
        data_array[~mask_array] = np.nan
    return np.asarray(data_array.reshape(*shape, order="F"))


def pyvista_mesh_to_mri(
    mesh: pv.DataSet, point_data_names: str | list[str], reference_mri: sm.SimpleMRI
) -> sm.SimpleMRI:
    if isinstance(point_data_names, str):
        point_data_names = [point_data_names]

    # Keep only the desired point data fields for sampling.
    newgrid = mesh.copy(deep=False)
    newgrid.point_data.clear()
    newgrid.cell_data.clear()
    for data_name in point_data_names:
        newgrid.point_data[data_name] = mesh.point_data[data_name]

    shape = reference_mri.shape
    affine = reference_mri.affine

    image_grid = pv.ImageData(dimensions=shape).transform(affine, inplace=False)
    results = image_grid.sample(newgrid, progress_bar=False, locator="static_cell")
    return {
        data_name: sm.SimpleMRI(mri_data_to_ndarray(results, data_name, shape), affine)
        for data_name in point_data_names
    }


@click.command()
@click.option("--vtk_path", type=Path, required=True)
@click.option("--data_name", type=str, required=True)
@click.option("--reference_mri", type=Path, required=True)
@click.option("--output", type=Path, required=True)
def vtk2mri(vtk_path: Path, data_name: str, reference_mri: Path, output: Path):
    mesh = pv.read(vtk_path)
    ref_mri = sm.load_mri(reference_mri, dtype=np.single)
    newmris = pyvista_mesh_to_mri(mesh, data_name, ref_mri)
    sm.save_mri(newmris[data_name], output, np.single)


if __name__ == "__main__":
    vtk2mri()
