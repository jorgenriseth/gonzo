import itertools
from pathlib import Path

import numpy as np
import scipy
import skimage
import tqdm

from gonzo.utils import apply_affine, largest_island
from gonzo.simple_mri import (
    load_mri,
    SimpleMRI,
    save_mri,
    assert_same_space,
    change_of_coordinates_map,
    data_reorientation,
)

MASK_DTYPE = np.uint8
SEG_DTYPE = np.int16
DATA_DTYPE = np.single


def seg_upsampling(
    reference: Path,
    segmentation: Path,
) -> SimpleMRI:
    seg_mri = load_mri(segmentation, SEG_DTYPE)
    reference_mri = load_mri(reference, DATA_DTYPE)

    shape_in = seg_mri.shape
    shape_out = reference_mri.shape

    upsampled_inds = np.fromiter(
        itertools.product(*(np.arange(ni) for ni in shape_out)),
        dtype=np.dtype((int, 3)),
    )

    seg_inds = apply_affine(
        np.linalg.inv(seg_mri.affine),
        apply_affine(reference_mri.affine, upsampled_inds),
    )
    seg_inds = np.rint(seg_inds).astype(int)

    # The two images does not necessarily share field of view.
    # Remove voxels which are not located within the segmentation fov.
    valid_index_mask = (seg_inds > 0).all(axis=1) * (seg_inds < shape_in).all(axis=1)
    upsampled_inds = upsampled_inds[valid_index_mask]
    seg_inds = seg_inds[valid_index_mask]

    I_in, J_in, K_in = seg_inds.T
    I_out, J_out, K_out = upsampled_inds.T

    seg_upsampled = np.zeros(shape_out, dtype=SEG_DTYPE)
    seg_upsampled[I_out, J_out, K_out] = seg_mri[I_in, J_in, K_in]
    upsampled_seg_mri = SimpleMRI(seg_upsampled, reference_mri.affine)
    assert_same_space(upsampled_seg_mri, reference_mri)
    return upsampled_seg_mri


def csf_segmentation(
    seg_upsampled_mri: SimpleMRI,
    csf_mask_mri: SimpleMRI,
) -> SimpleMRI:
    assert_same_space(seg_upsampled_mri, csf_mask_mri)
    I, J, K = np.where(seg_upsampled_mri.data != 0)
    inds = np.array([I, J, K]).T
    interp = scipy.interpolate.NearestNDInterpolator(inds, seg_upsampled_mri[I, J, K])
    i, j, k = np.where(csf_mask.data)
    csf_seg = np.zeros_like(seg_upsampled_mri.data)
    csf_seg[i, j, k] = interp(i, j, k)
    return SimpleMRI(csf_seg, csf_mask_mri.affine)


def segmentation_refinement(
    upsampled_segmentation: SimpleMRI,
    csf_segmentation: SimpleMRI,
    closing_radius: int = 5,
) -> SimpleMRI:
    combined_segmentation = skimage.segmentation.expand_labels(
        upsampled_segmentation.data, distance=3
    )
    csf_mask = csf_segmentation.data != 0
    combined_segmentation[csf_mask] = -csf_seg[csf_mask]

    radius = closing_radius
    combined_mask = csf_mask + (upsampled_segmentation.data != 0)
    combined_mask = skimage.morphology.closing(
        combined_mask,
        footprint=np.ones([1 + radius * 2] * combined_mask.ndim),
    )
    combined_segmentation[~combined_mask] = 0
    aseg_new = np.where(combined_segmentation > 0, combined_segmentation, 0)
    return SimpleMRI(aseg_new, upsampled_segmentation.affine)


def segmentation_smoothing(
    segmentation: np.ndarray, sigma: float, cutoff_score: float = 0.5, **kwargs
) -> dict[str, np.ndarray]:
    labels = np.unique(segmentation)
    labels = labels[labels != 0]
    new_labels = np.zeros_like(segmentation)
    high_scores = np.zeros(segmentation.shape)
    for label in tqdm.tqdm(labels):
        label_scores = scipy.ndimage.gaussian_filter(
            (segmentation == label).astype(float), sigma=sigma, **kwargs
        )
        is_new_high_score = label_scores > high_scores
        new_labels[is_new_high_score] = label
        high_scores[is_new_high_score] = label_scores[is_new_high_score]

    delete_scores = (high_scores < cutoff_score) * (segmentation == 0)
    new_labels[delete_scores] = 0
    return {"labels": new_labels, "scores": high_scores}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--fs_seg", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--csfmask", type=Path, required=True)
    parser.add_argument("--output_seg", type=Path, required=True)
    parser.add_argument("--output_csfseg", type=Path, required=True)
    parser.add_argument("--label_smoothing", type=float, default=0)
    args = parser.parse_args()

    upsampled_seg = seg_upsampling(args.reference, args.fs_seg)
    if args.label_smoothing > 0:
        upsampled_seg.data = segmentation_smoothing(
            upsampled_seg.data, sigma=args.label_smoothing
        )["labels"]
    csf_mask = load_mri(args.csfmask, dtype=bool)
    csf_seg = csf_segmentation(upsampled_seg, csf_mask)
    save_mri(csf_seg, args.output_csfseg, dtype=SEG_DTYPE)

    refined_seg = segmentation_refinement(upsampled_seg, csf_seg)
    save_mri(refined_seg, args.output_seg, dtype=SEG_DTYPE)
