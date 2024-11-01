import pyvista as pv
import numpy as np
from pathlib import Path

from simple_mri import load_mri, SimpleMRI, save_mri, assert_same_space

import skimage.morphology as skim
import skimage
import scipy.ndimage as ndi


V3 = 14
V4 = 15
LEFT_LV = 4
LEFT_ILV = 5
RIGHT_LV = 43
RIGHT_ILV = 44
CSF_generic = 24


def extract_ventricle_surface(
    aseg_mri: SimpleMRI,
    ilv_connection_radius: int = 3,
    lv_closing_radius: int = 5,
    v3_lv_connection_radius: int = 3,
    aqueduct_radius: int = 2,
    ventricle_dilation_radius: int = 0,
) -> pv.PolyData:
    aseg, affine = aseg_mri.data, aseg_mri.affine
    left_lv = skimage.morphology.binary_closing(
        (aseg == LEFT_LV)
        + connect_region_by_lines(
            aseg == LEFT_ILV, 2, line_radius=ilv_connection_radius
        ),
        skimage.morphology.ball(lv_closing_radius),
    )
    right_lv = skimage.morphology.binary_closing(
        (aseg == RIGHT_LV)
        + connect_region_by_lines(
            aseg == RIGHT_ILV, 2, line_radius=ilv_connection_radius
        ),
        skimage.morphology.ball(lv_closing_radius),
    )
    V3_to_right_lv = connecting_line(
        np.isin(aseg, V3), right_lv, line_radius=v3_lv_connection_radius
    )
    V3_to_left_lv = connecting_line(
        np.isin(aseg, V3), left_lv, line_radius=v3_lv_connection_radius
    )
    aqueduct = connecting_line(
        np.isin(aseg, V3), np.isin(aseg, V4), line_radius=aqueduct_radius
    )
    ventricle_mask = (
        np.isin(aseg, V3 + V4)
        + aqueduct
        + left_lv
        + right_lv
        + V3_to_right_lv
        + V3_to_left_lv
    )
    if ventricle_dilation_radius > 0:
        ventricle_mask = skim.binary_dilation(
            ventricle_mask, footprint=skim.ball(ventricle_dilation_radius)
        )
    elif ventricle_dilation_radius < 0:
        ventricle_mask = skim.binary_erosion(
            ventricle_mask, footprint=skim.ball(ventricle_dilation_radius)
        )
    ventricle_surf = extract_surface(ventricle_mask)
    ventricle_surf.transform(affine)
    ventricle_surf.compute_normals(inplace=True, flip_normals=False)
    return ventricle_surf


def connect_region_by_lines(mask, connectivity, line_radius: float):
    labeled_mask = skimage.measure.label(mask, connectivity=connectivity)
    mask = mask.copy()
    while len(np.unique(labeled_mask)) > 2:
        R1 = labeled_mask == 1
        R2 = mask * (~R1)
        conn = connecting_line(R1, R2, line_radius)
        mask += conn
        labeled_mask = skimage.measure.label(mask, connectivity=connectivity)
    return mask


def extract_surface(
    img, resolution=(1, 1, 1), origin=(-0.5, -0.5, -0.5)
) -> pv.PolyData:
    grid = pv.ImageData(dimensions=img.shape, spacing=resolution, origin=origin)
    mesh = grid.contour([0.5], img.flatten(order="F"), method="marching_cubes")
    surf = mesh.extract_geometry()
    surf.clear_data()
    return surf


def connecting_line(R1, R2, line_radius):
    pointa = get_closest_point(R1, R2, R1.shape)
    pointb = get_closest_point(R2, R1, R2.shape)
    ii, jj, kk = np.array(skimage.draw.line_nd(pointa, pointb, endpoint=True))
    conn = np.zeros(R1.shape, dtype=bool)
    conn[ii, jj, kk] = True
    conn = skim.binary_dilation(conn, footprint=skim.ball(line_radius))
    return conn


def get_closest_point(a: np.ndarray, b: np.ndarray, img_shape: tuple[int, ...]):
    dist = ndi.distance_transform_edt(~a)
    if type(dist) is np.ndarray:
        dist[~b] = np.inf
    else:
        raise ValueError("Invalid return from distance transform")
    minidx = np.unravel_index(np.argmin(dist), img_shape)
    return minidx


# def region_number_of_components(mask, connectivity):
#     labeled_mask = skimage.measure.label(mask, connectivity=connectivity)
#     regions = skimage.measure.regionprops(labeled_mask)
#     return len(regions)

# def connect_regions_by_closing(mask: np.ndarray, connectivity, min_radius=1, max_radius=5, return_best=False):
#     if region_number_of_components(mask, connectivity)  == 0:
#         raise ValueError("No regions in input mask")
#     newmask = mask
#     for r in range(min_radius, max_radius+1):
#         newmask = skimage.morphology.binary_closing(newmask, skimage.morphology.ball(r))
#         if region_number_of_components(mask, connectivity) == 2:
#             return newmask
#     e = f"Couldn't connect regions through closing with radius {r}"
#     if return_best:
#         return newmask
#     raise RuntimeError(e)


if __name__ == "__main__":
    import click

    @click.command()
    @click.option("--aseg", type=Path, required=True)
    @click.option("--output", type=Path, required=True)
    def main(
        aseg_path: Path,
        output_path: Path,
        ilv_connection_radius: int = 3,
        lv_closing_radius: int = 5,
        aqueduct_radius: int = 1,
        ventricle_dilation_radius: int = 0,
    ):
        aseg_mri = load_mri(aseg_path, dtype=np.int16)
        ventricle_surf = extract_ventricle_surface(
            aseg_mri,
            ilv_connection_radius,
            lv_closing_radius,
            aqueduct_radius,
            ventricle_dilation_radius,
        )
        pv.save_meshio(output_path, ventricle_surf)
