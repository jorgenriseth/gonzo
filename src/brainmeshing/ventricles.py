from pathlib import Path
from typing import Optional

import click
import numpy as np
import pyvista as pv
import scipy
import skimage
from simple_mri import SimpleMRI, load_mri
from gonzo.utils import segmentation_smoothing

V3 = 14
V4 = 15
LEFT_LV = 4
LEFT_ILV = 5
RIGHT_LV = 43
RIGHT_ILV = 44
CSF_generic = 24

VENTRICLES = [LEFT_LV, LEFT_ILV, RIGHT_LV, RIGHT_ILV, V3, V4]


@click.command(name="ventricle-surf")
@click.option("-i", "--input", type=Path, required=True)
@click.option("-o", "--output", type=Path, required=True)
@click.option("--min_radius", type=int, default=2)
@click.option("--initial_smoothing", type=float, default=0)
@click.option("--surface_smoothing", type=float, default=0)
@click.option("--taubin_iter", type=int, default=0)
@click.option("--dilate", type=int, default=0)
@click.option("--voxelized", type=bool, is_flag=True)
def main(input: Path, output: Path, **kwargs):
    Path(output).parent.mkdir(exist_ok=True)
    seg_mri = load_mri(input, dtype=np.int16)
    surf = extract_ventricle_surface(seg_mri, **kwargs)
    surf.compute_normals(
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
    pv.save_meshio(output, surf)


def extract_ventricle_surface(
    seg_mri: SimpleMRI,
    initial_smoothing: float,
    min_radius: int,
    surface_smoothing: float,
    taubin_iter: int = 0,
    dilate: int = 0,
    voxelized: bool = False,
) -> pv.PolyData:
    seg, affine = seg_mri.data, seg_mri.affine
    if initial_smoothing > 0:
        seg = segmentation_smoothing(seg, sigma=initial_smoothing)["labels"]
    ventricle_seg = refine_ventricle_segments(seg, min_radius=min_radius, dilate=dilate)
    surf = binary_image_surface_extraction(
        ventricle_seg > 0, sigma=surface_smoothing, cutoff=0.5, to_cell=voxelized
    ).triangulate()
    if taubin_iter > 0:
        surf.smooth_taubin(taubin_iter, inplace=True)
    return surf.transform(affine)


def refine_ventricle_segments(
    seg: np.ndarray, min_radius: int, dilate: int
) -> np.ndarray:
    ilv = extract_and_connect_inferior_lateral_ventricle(seg, min_radius)
    aqueduct = connecting_line(seg == V3, seg == V4, line_radius=min_radius)
    v4_with_aqueduct = expand_to_minimum(aqueduct + (seg == V4), min_radius=min_radius)
    v3_lateral_connection = enlarge_v3_lateral_connection(seg, min_radius)
    ventricle_seg = (
        np.isin(seg, VENTRICLES)
        + ilv["right"]
        + ilv["left"]
        + v4_with_aqueduct
        + v3_lateral_connection
    )
    if dilate > 0:
        ventricle_seg = skimage.morphology.binary_dilation(
            ventricle_seg, skimage.morphology.ball(dilate)
        )
    return ventricle_seg


def extract_and_connect_inferior_lateral_ventricle(
    seg: np.ndarray, min_radius: int
) -> dict[str, np.ndarray]:
    left_ilv = connect_region_by_lines(seg == LEFT_ILV, 2, line_radius=min_radius)
    right_ilv = connect_region_by_lines(seg == RIGHT_ILV, 2, line_radius=min_radius)
    left_ilv = expand_to_minimum(left_ilv, min_radius)
    right_ilv = expand_to_minimum(right_ilv, min_radius)
    return {"left": left_ilv, "right": right_ilv}


def enlarge_v3_lateral_connection(
    seg: np.ndarray, connection_radius: int
) -> np.ndarray:
    enlarged_v3 = seg == V3
    left_conn = connecting_line(
        enlarged_v3, seg == LEFT_LV, line_radius=connection_radius
    )
    right_conn = connecting_line(
        enlarged_v3, seg == RIGHT_LV, line_radius=connection_radius
    )
    return right_conn + left_conn


def image_data_to_grid(
    vol: np.ndarray, to_cell: bool = False, data_label: Optional[str] = None
) -> pv.ImageData:
    label = "labels" if data_label is None else data_label
    point_volume = pv.ImageData(dimensions=vol.shape, spacing=[1] * 3, origin=[0] * 3)
    point_volume.point_data[label] = vol.ravel(order="F")
    if to_cell:
        return point_volume.points_to_cells()
    return point_volume


def binary_image_surface_extraction(
    vol: np.ndarray, sigma: float = 0, cutoff=0.5, to_cell: bool = False
) -> pv.PolyData:
    grid = pv.ImageData(dimensions=vol.shape, spacing=[1] * 3, origin=[0] * 3)
    if sigma > 0:
        grid["labels"] = skimage.filters.gaussian(vol, sigma=sigma).ravel(order="F")
    else:
        grid["labels"] = vol.ravel(order="F")
    if to_cell:
        thresh = grid.points_to_cells().threshold(cutoff)
        surf = thresh.extract_surface()  # type: ignore
    else:
        surf = grid.contour([cutoff])  # type: ignore
    surf.clear_data()  # type: ignore
    return surf


def connect_region_by_lines(
    mask: np.ndarray, connectivity: int, line_radius: int
) -> np.ndarray:
    labeled_mask = skimage.measure.label(mask, connectivity=connectivity)
    mask = mask.copy()
    while len(np.unique(labeled_mask)) > 2:
        R1 = labeled_mask == 1
        R2 = mask * (~R1)
        conn = connecting_line(R1, R2, line_radius)
        mask += conn
        labeled_mask = skimage.measure.label(mask, connectivity=connectivity)
    return mask


def connecting_line(R1: np.ndarray, R2: np.ndarray, line_radius: int) -> np.ndarray:
    pointa = get_closest_point(R1, R2, R1.shape)
    pointb = get_closest_point(R2, R1, R2.shape)
    ii, jj, kk = np.array(skimage.draw.line_nd(pointa, pointb, endpoint=True))
    conn = np.zeros(R1.shape, dtype=bool)
    conn[ii, jj, kk] = True
    conn = skimage.morphology.binary_dilation(
        conn, footprint=skimage.morphology.ball(line_radius)
    )
    return conn


def get_closest_point(
    a: np.ndarray, b: np.ndarray, img_shape: tuple[int, ...]
) -> tuple[np.intp, ...]:
    dist = scipy.ndimage.distance_transform_edt(~a)
    if type(dist) is np.ndarray:
        dist[~b] = np.inf
    else:
        raise ValueError("Invalid return from distance transform")
    minidx = np.unravel_index(np.argmin(dist), img_shape)
    return minidx


def expand_to_minimum(binary: np.ndarray, min_radius: int) -> np.ndarray:
    skeleton = skimage.morphology.skeletonize(binary)
    skeleton = skimage.morphology.binary_dilation(
        skeleton, skimage.morphology.ball(min_radius)
    )
    return binary + skeleton
