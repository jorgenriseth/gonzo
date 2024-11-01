import tempfile
from pathlib import Path
from typing import Any, Optional

import click
import numpy as np
import pyvista as pv
from simple_mri import load_mri

from brainmeshing.surfaces import (
    TaubinParams,
    hemisphere_surface_refinement,
    pial_surface_processing,
    subcortical_gray_surfaces,
)


@click.command("gm-surfaces")
@click.option("--inputdir", type=Path, required=True)
@click.option("--seg", type=Path, required=True)
@click.option("--ventricles", type=Path, required=True)
@click.option("--outputdir", type=Path, required=True)
@click.option("--edge_length", type=float, default=0.5)
@click.option("--remesh_iter", type=int, default=1)
@click.option("--gapsize", type=float, default=0.2)
@click.option("--pial_taubin_n", type=int, default=100)
@click.option("--pial_taubin_pass_band", type=float, default=0.1)
@click.option("--subcort_sigma", type=float, default=1.0)
@click.option("--subcort_presmooth_n", type=int, default=10)
@click.option("--subcort_presmooth_pass_band", type=float, default=0.1)
@click.option("--subcort_postsmooth_n", type=int, default=100)
@click.option("--subcort_postsmooth_pass_band", type=float, default=0.1)
@click.option("--tmpdir", type=Path)
def main(
    inputdir: Path,
    seg: Path,
    ventricles: Path,
    outputdir: Path,
    edge_length: float,
    remesh_iter: int,
    gapsize: float,
    pial_taubin_n: int,
    pial_taubin_pass_band: float,
    subcort_sigma: float,
    subcort_presmooth_n: int,
    subcort_presmooth_pass_band: float,
    subcort_postsmooth_n: int,
    subcort_postsmooth_pass_band: float,
    tmpdir: Optional[Path] = None,
):
    tempdir = tempfile.TemporaryDirectory()
    tmppath = Path(tempdir.name) if tmpdir is None else tmpdir
    outputdir.mkdir(exist_ok=True)
    ventricle_surf = pv.read(ventricles)
    seg_mri = load_mri(seg, dtype=np.int16)
    hemisphere_surface_refinement(
        inputdir / "lh_pial.stl",
        inputdir / "rh_pial.stl",
        tmppath,
        max_edge_length=edge_length,
        remesh_iter=remesh_iter,
        fix_boundaries=False,
        gapsize=gapsize,
        overlapping=True,
    )
    lh_pial_refined = pv.read(tmppath / "lh_pial_refined.stl")
    lh_pial_novent = pial_surface_processing(
        lh_pial_refined, ventricle_surf, pial_taubin_n, pial_taubin_pass_band
    )
    pv.save_meshio(outputdir / "lh_pial_novent.stl", lh_pial_novent)

    rh_pial_refined = pv.read(tmppath / "rh_pial_refined.stl")
    rh_pial_novent = pial_surface_processing(
        rh_pial_refined, ventricle_surf, pial_taubin_n, pial_taubin_pass_band
    )
    pv.save_meshio(outputdir / "rh_pial_novent.stl", rh_pial_novent)

    subcortical_gm = subcortical_gray_surfaces(
        seg_mri,
        subcort_sigma,
        TaubinParams(subcort_presmooth_n, subcort_presmooth_pass_band),
        TaubinParams(subcort_postsmooth_n, subcort_postsmooth_pass_band),
    )
    pv.save_meshio(outputdir / "subcortical_gm.stl", subcortical_gm)


if __name__ == "__main__":
    main()
