import tempfile
from pathlib import Path
from typing import Optional

import click
import numpy as np
import pymeshfix
import pyvista as pv
import SVMTK as svmtk
import tqdm
from loguru import logger

from brainmeshing.surfaces import fs_surf_to_stl, pyvista2svmtk, svmtk2pyvista


@click.command("separate-surfaces")
@click.option("--fs_dir", type=Path, required=True)
@click.option("--outputdir", type=Path, required=True)
@click.option("--tmpdir", type=Path)
def main(fs_dir: Path, outputdir: Path, tmpdir: Optional[Path]):
    tempdir = tempfile.TemporaryDirectory()
    tmppath = Path(tempdir.name) if tmpdir is None else tmpdir
    fs_surf_to_stl(fs_dir / "surf", tmppath)
    separate_white_and_gray_surfaces(
        tmppath / "lh_pial.stl",
        tmppath / "lh_white.stl",
        outputdir / "lh_pial.stl",
        outputdir / "lh_white.stl",
    )
    separate_white_and_gray_surfaces(
        tmppath / "rh_pial.stl",
        tmppath / "rh_white.stl",
        outputdir / "rh_pial.stl",
        outputdir / "rh_white.stl",
    )


def separate_white_and_gray_surfaces(pial_in, white_in, pial_out, white_out):
    logger.info(f"Separating surfaces {pial_in}, {white_in}")
    pial = svmtk.Surface(str(pial_in))
    white = svmtk.Surface(str(white_in))

    pial_grid = svmtk2pyvista(pial)
    white_grid = svmtk2pyvista(white)
    pial_grid.compute_normals(
        inplace=True, auto_orient_normals=True, consistent_normals=True
    )
    white_grid.compute_normals(
        inplace=True, auto_orient_normals=True, consistent_normals=True
    )
    pial_grid.compute_implicit_distance(white_grid, inplace=True)
    white_grid.compute_implicit_distance(pial_grid, inplace=True)

    logger.info("Finding pial degeneracies")
    pial_degenerate = pial_grid.extract_points(
        np.where(pial_grid.point_data["implicit_distance"] < 0)
    )
    white_degenerate = white_grid.extract_points(
        np.where(white_grid.point_data["implicit_distance"] > 0)
    )
    _, closest_points = (pial_degenerate + white_degenerate).find_closest_cell(
        pial_grid.points, return_closest_point=True
    )
    d_exact = np.linalg.norm(pial_grid.points - closest_points, axis=1)

    pial_degenerate_neighbourhood = pial_grid.extract_points(np.where(d_exact < 0.5))
    all_regions = pial_degenerate_neighbourhood.connectivity("all")
    region_ids = np.unique(all_regions["RegionId"])
    regions = [
        all_regions.extract_points(
            np.where(all_regions.point_data["RegionId"] == label)
        )
        for label in region_ids
    ]

    logger.info(f"Patching {len(region_ids)} pial degeneracies")
    new_pial_svm = pyvista2svmtk(pial_grid)
    for region in tqdm.tqdm(regions):
        patch = pyvista2svmtk(region).convex_hull()
        patch.isotropic_remeshing(1.0, 1, True)
        new_pial_svm.union(patch)
    new_pial = repair_triangulation(svmtk2pyvista(new_pial_svm))
    new_pial.subdivide_adaptive(max_tri_area=3, inplace=True)
    pv.save_meshio(pial_out, new_pial)

    logger.info("Finding white degeneracies")
    # White surface fixing
    all_idcs = white_grid.point_data["vtkOriginalPointIds"][
        white_degenerate.point_data["vtkOriginalPointIds"]
    ]
    neighbor_idcs = np.unique(
        np.concatenate(
            [
                sum(white_grid.point_neighbors_levels(idx, 1), start=[])
                for idx in all_idcs
            ]
        )
    )
    white_degenerate_neighbourhood = white_grid.extract_points(neighbor_idcs)
    all_regions = white_degenerate_neighbourhood.connectivity("all")
    region_ids = np.unique(all_regions.point_data["RegionId"])
    regions = [
        all_regions.extract_points(
            np.where(all_regions.point_data["RegionId"] == label)
        )
        for label in region_ids
    ]
    holey_white, ridx = white_grid.remove_points(
        white_degenerate_neighbourhood.point_data["vtkOriginalPointIds"]
    )
    logger.info("Patching holes in white surface")
    new_white_svm = pyvista2svmtk(holey_white)
    new_white_svm.fill_holes()
    new_white_svm = pyvista2svmtk(
        svmtk2pyvista(new_white_svm).subdivide_adaptive(max_edge_len=2)
    )
    new_white = repair_triangulation(svmtk2pyvista(new_white_svm))
    new_white.subdivide_adaptive(max_tri_area=3, inplace=True)
    pv.save_meshio(white_out, new_white)
    logger.info(f"Finished separating with {pial_in}, {white_in}")
    print()


def repair_triangulation(mesh):
    v, f = mesh.points, mesh.faces
    f = mesh.faces.reshape((-1, 4))[:, 1:]

    meshfix = pymeshfix.MeshFix(v, f)
    meshfix.repair()

    num_points_stack = 3 * np.ones(
        (meshfix.faces.shape[0], 1), dtype=meshfix.faces.dtype
    )
    pv_faces = np.concatenate((num_points_stack, meshfix.faces), axis=1).ravel()
    return pv.PolyData(meshfix.v, pv_faces)


if __name__ == "__main__":
    main()
