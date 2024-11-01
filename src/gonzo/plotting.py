from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib as mpl
import numpy as np
import pandas as pd
import nibabel.nifti1 as nifti1
import skimage

mpl.rcParams.update({"font.size": 14})


def plotting_oriented(volume, orientation):
    if orientation == "sagittal":
        return volume.transpose(0, 2, 1)[:, ::-1, ::-1]
    elif orientation == "coronal":
        return volume.transpose(1, 2, 0)[:, ::-1, :]
    elif orientation == "axial":
        return volume.transpose(2, 1, 0)[:, ::-1, :]
    raise ValueError(f"invalid orientation {orientation}")


def crop_limits(im, crop_margin):
    try:
        thresh = skimage.filters.threshold_triangle(np.where(np.isnan(im), 0, im))
    except ValueError:
        return 0, im.shape[0], 0, im.shape[1]
    binary = im > thresh
    binary = skimage.filters.gaussian(binary, 5)
    try:
        binary = binary > skimage.filters.threshold_isodata(binary)
    except IndexError:
        return 0, im.shape[0], 0, im.shape[1]
    bounds_i, bounds_j = [(min(x), max(x)) for x in np.where(binary)]
    crop_i = int(max(0, bounds_i[0] - crop_margin)), int(bounds_i[1] + crop_margin)
    crop_j = int(max(0, bounds_j[0] - crop_margin)), int(bounds_j[1] + crop_margin)
    return *crop_i, *crop_j


def image_grid_builder(fig_width, im_width, im_height, grid_config, frame=False):
    body_width = grid_config["ncols"] * im_width
    body_height = grid_config["nrows"] * im_height

    col_widths = [
        *[
            grid_config[prop] * body_width
            for prop in ["fig_left_margin", "row_left_margin"]
        ],
        *([im_width] * grid_config["ncols"]),
        *[
            grid_config[prop] * body_width
            for prop in ["row_right_margin", "fig_right_margin"]
        ],
    ]
    row_heights = [
        *[
            grid_config[prop] * body_height
            for prop in ["fig_top_margin", "col_top_margin"]
        ],
        *([im_height] * grid_config["nrows"]),
        *[
            grid_config[prop] * body_height
            for prop in ["col_bottom_margin", "fig_bottom_margin"]
        ],
    ]

    total_width = sum(col_widths)
    total_height = sum(row_heights)
    aspect_ratio = total_width / total_height
    fig_height = fig_width / aspect_ratio

    col_widths = np.array(col_widths) / total_width
    row_heights = np.array(row_heights) / total_height
    col_offsets = np.cumsum([0] + list(col_widths[:-1]))
    row_offsets = 1 - np.cumsum(row_heights)

    fig = plt.figure(figsize=(fig_width, fig_height))
    axes = {
        "fig_top": fig.add_axes(
            (col_offsets[2], row_offsets[0], sum(col_widths[2:-2]), row_heights[0]),
            xticks=[],
            yticks=[],
            frameon=frame,
        ),
        "fig_bottom": fig.add_axes(
            (col_offsets[2], row_offsets[-1], sum(col_widths[2:-2]), row_heights[-1]),
            xticks=[],
            yticks=[],
            frameon=frame,
        ),
        "fig_left": fig.add_axes(
            (col_offsets[0], row_offsets[-3], col_widths[0], sum(row_heights[2:-2])),
            xticks=[],
            yticks=[],
            frameon=frame,
        ),
        "fig_right": fig.add_axes(
            (col_offsets[-1], row_offsets[-3], col_widths[-1], sum(row_heights[2:-2])),
            xticks=[],
            yticks=[],
            frameon=frame,
        ),
        "col_top": [
            fig.add_axes(
                (
                    col_offsets[2 + idx],
                    row_offsets[1],
                    col_widths[2 + idx],
                    row_heights[1],
                ),
                xticks=[],
                yticks=[],
                frameon=frame,
            )
            for idx in range(grid_config["ncols"])
        ],
        "col_bottom": [
            fig.add_axes(
                (
                    col_offsets[2 + idx],
                    row_offsets[-2],
                    col_widths[2 + idx],
                    row_heights[-2],
                ),
                xticks=[],
                yticks=[],
                frameon=frame,
            )
            for idx in range(grid_config["ncols"])
        ],
        "row_left": [
            fig.add_axes(
                (
                    col_offsets[1],
                    row_offsets[2 + idx],
                    col_widths[1],
                    row_heights[2 + idx],
                ),
                xticks=[],
                yticks=[],
                frameon=frame,
            )
            for idx in range(grid_config["nrows"])
        ],
        "row_right": [
            fig.add_axes(
                (
                    col_offsets[-2],
                    row_offsets[2 + idx],
                    col_widths[-2],
                    row_heights[2 + idx],
                ),
                xticks=[],
                yticks=[],
                frameon=frame,
            )
            for idx in range(grid_config["nrows"])
        ],
        "body": [
            fig.add_axes(
                (
                    col_offsets[2 + col],
                    row_offsets[2 + row],
                    col_widths[2 + col],
                    row_heights[2 + row],
                ),
                xticks=[],
                yticks=[],
            )
            for row, col in map(
                lambda idx: (idx // grid_config["ncols"], idx % grid_config["ncols"]),
                range(grid_config["nrows"] * grid_config["ncols"]),
            )
        ],
    }
    return fig, axes
