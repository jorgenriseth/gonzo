import dataclasses
import functools
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pyvista as pv
import SVMTK as svmtk
from gonzo.segmentation_groups import default_segmentation_groups
from gonzo.simple_mri import SimpleMRI
from gonzo.utils import grow_restricted
from loguru import logger

from brainmeshing.ventricles import binary_image_surface_extraction

WHITE = [2, 41]
CEREBRAL_CORTEX = [3, 42]
LATERAL_VENTRICLES = [4, 43]
GENERIC_CSF = [24]
CC = [251, 252, 253, 254, 255]
DC = [28, 60]


def fs_surf_to_stl(fs_surface_dir: Path, output_dir: Path, verbose: bool = False):
    fs_surfaces = ["rh.pial", "lh.pial", "rh.white", "lh.white"]
    logger.info("Converting FS-surfaces to .stl")
    for surface in fs_surfaces:
        input = fs_surface_dir / surface
        output = (output_dir / surface.replace(".", "_")).with_suffix(".stl")
        redirect = ">> /dev/null" if not verbose else ""
        subprocess.run(
            f"mris_convert --to-scanner {input} {output} {redirect}",
            shell=True,
        ).check_returncode()


def surface_refinement(
    input: Path,
    max_edge_length: float,
    remesh_iter: int,
    laplace_eps: float,
    laplace_iter: int,
    taubin_iter: int,
    fix_boundaries: bool,
    gapsize: float,
):
    assert Path(input).exists(), f"{input} does not exist"
    surface = svmtk.Surface(str(input))
    if max_edge_length > 0 and remesh_iter > 0:
        surface.isotropic_remeshing(max_edge_length, remesh_iter, fix_boundaries)
    if laplace_eps > 0:
        surface.smooth_laplacian(laplace_eps, laplace_iter)
    if taubin_iter > 0 and laplace_iter > 0:
        surface.smooth_taubin(taubin_iter)
    surface.fill_holes()
    if gapsize != 0:
        surface.separate_narrow_gaps(-abs(gapsize))
    return surface


def hemisphere_surface_refinement(
    lh_path: Path,
    rh_path: Path,
    outputdir: Path,
    max_edge_length: float,
    remesh_iter: int,
    fix_boundaries: bool,
    gapsize: float,
    overlapping: bool,
):
    logger.info("Refining left hemisphere..")
    lh = surface_refinement(
        lh_path, max_edge_length, remesh_iter, 0, 0, 0, fix_boundaries, gapsize
    )
    logger.info("Refining right hemisphere..")
    rh = surface_refinement(
        rh_path, max_edge_length, remesh_iter, 0, 0, 0, fix_boundaries, gapsize
    )
    logger.info("Separating hemispheres")
    if overlapping:
        svmtk.separate_overlapping_surfaces(lh, rh)
    else:
        svmtk.separate_close_surfaces(lh, rh)
    logger.info("Saving hemispheres")
    lh.save(str(outputdir / f"{lh_path.stem}_refined.stl"))
    rh.save(str(outputdir / f"{rh_path.stem}_refined.stl"))


def grow_white_connective_tissue(
    seg_mri: SimpleMRI,
):
    CC_mask = grow_restricted(
        np.isin(seg_mri.data, CC), np.isin(seg_mri.data, WHITE + [24]), 2
    )
    LV_mask = grow_restricted(
        np.isin(seg_mri.data, LATERAL_VENTRICLES),
        ~np.isin(seg_mri.data, CEREBRAL_CORTEX),
        3,
    )
    surf = binary_image_surface_extraction(LV_mask + CC_mask, sigma=1)
    return surf.transform(seg_mri.affine)


def pyvista2svmtk(
    pv_grid: pv.DataObject, suffix: Optional[str] = None
) -> svmtk.Surface:
    ft = ".stl" if suffix is None else suffix
    with tempfile.TemporaryDirectory() as tmp_path:
        tmpfile = Path(tmp_path) / f"tmpsurf{ft}"
        pv.save_meshio(tmpfile, pv_grid)
        svmtk_grid = svmtk.Surface(str(tmpfile))
    return svmtk_grid


def svmtk2pyvista(
    svmtk_surface: svmtk.Surface, suffix: Optional[str] = None
) -> pv.DataObject:
    ft = ".stl" if suffix is None else suffix
    with tempfile.TemporaryDirectory() as tmp_path:
        tmpfile = Path(tmp_path) / f"tmpsurf{ft}"
        svmtk_surface.save(str(tmpfile))
        pv_grid = pv.read(tmpfile)
    return pv_grid


def surface_union(*args):
    surfaces = [pyvista2svmtk(surf) for surf in args]
    for surface in surfaces[1:]:
        surfaces[0].union(surface)
    return surfaces[0]


@dataclasses.dataclass
class TaubinParams:
    n_iter: int
    pass_band: float
    normalize: bool = True


def pial_surface_processing(pial, ventricles, taubin_iter, taubin_pass_band):
    ventricles_svm = pyvista2svmtk(ventricles)
    svm_surface = pyvista2svmtk(pial)
    svm_surface.difference(ventricles_svm)
    svm_surface.separate_close_vertices()
    pv_surface = svmtk2pyvista(svm_surface)
    pv_surface.compute_normals(auto_orient_normals=True, inplace=True)
    return pv_surface.smooth_taubin(
        taubin_iter, taubin_pass_band, normalize_coordinates=True
    )


def subcortical_gray_surfaces(
    seg_mri: SimpleMRI, sigma: float, presmooth: TaubinParams, postsmooth: TaubinParams
) -> Any:
    subcortical_surfaces = [
        binary_image_surface_extraction(np.isin(seg_mri.data, region), sigma=sigma)
        for region in default_segmentation_groups()["basal-ganglias"]
    ]
    if presmooth.n_iter > 0:
        for surf in subcortical_surfaces:
            surf.smooth_taubin(
                presmooth.n_iter,
                presmooth.pass_band,
                normalize_coordinates=True,
                inplace=True,
            )

    subcortical_gm = functools.reduce(lambda x, y: x + y, subcortical_surfaces)
    if postsmooth.n_iter > 0:
        subcortical_gm = subcortical_gm.smooth_taubin(
            presmooth.n_iter,
            presmooth.pass_band,
            normalize_coordinates=True,
            inplace=True,
        )
    return subcortical_gm.transform(seg_mri.affine)
