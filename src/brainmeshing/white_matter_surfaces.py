import tempfile
from pathlib import Path
from typing import Optional

import click
import numpy as np
import pyvista as pv
from simple_mri import load_mri

from brainmeshing.surfaces import (
    grow_white_connective_tissue,
    hemisphere_surface_refinement,
    pyvista2svmtk,
    surface_union,
    svmtk2pyvista,
)


@click.command("wm-surfaces")
@click.option("--inputdir", type=Path, required=True)
@click.option("--seg", type=Path, required=True)
@click.option("--ventricles", "--ventricle_surf", type=Path, required=True)
@click.option("--output", type=Path, required=True)
@click.option("--edge_length", type=float, default=0.5)
@click.option("--remesh_iter", type=int, default=1)
@click.option("--gapsize", type=float, default=0.2)
@click.option("--postsmooth_n", type=int, default=100)
@click.option("--postsmooth_pass_band", type=float, default=0.1)
@click.option("--tmpdir", type=Path)
def main(
    inputdir: Path,
    seg: Path,
    ventricles: Path,
    output: Path,
    edge_length: float,
    remesh_iter: int,
    gapsize: float,
    postsmooth_n: int,
    postsmooth_pass_band: int,
    tmpdir: Optional[Path] = None,
):
    tempdir = tempfile.TemporaryDirectory()
    tmppath = Path(tempdir.name) if tmpdir is None else tmpdir
    (output.parent).mkdir(exist_ok=True)
    ventricle_surf = pv.read(ventricles)
    seg_mri = load_mri(seg, dtype=np.int16)
    hemisphere_surface_refinement(
        inputdir / "lh_white.stl",
        inputdir / "rh_white.stl",
        tmppath,
        max_edge_length=edge_length,
        remesh_iter=remesh_iter,
        fix_boundaries=False,
        gapsize=gapsize,
        overlapping=True,
    )
    rh_white_refined = pv.read(tmppath / "rh_white_refined.stl")
    lh_white_refined = pv.read(tmppath / "lh_white_refined.stl")
    connective = grow_white_connective_tissue(seg_mri)
    white_svm = surface_union(lh_white_refined, connective, rh_white_refined)
    # white_svm.difference(pyvista2svmtk(ventricle_surf))
    white = svmtk2pyvista(white_svm)
    if postsmooth_n > 0:
        white.smooth_taubin(
            postsmooth_n, postsmooth_pass_band, normalize_coordinates=True, inplace=True
        )
    white.compute_normals(
        cell_normals=True,
        point_normals=True,
        split_vertices=False,
        flip_normals=False,
        consistent_normals=True,
        auto_orient_normals=True,
        non_manifold_traversal=True,
        feature_angle=30.0,
        inplace=True,
        progress_bar=False,
    )
    pv.save_meshio(output, white)


if __name__ == "__main__":
    main()
