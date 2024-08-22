import nibabel
import pydicom
import numpy as np
from pathlib import Path
from loguru import logger

from gonzo.simple_mri import data_reorientation, change_of_coordinates_map, SimpleMRI

VOLUME_LABELS = [
    "IR-modulus",
    "IR-real",
    "IR-corrected-real",
    "SE-modulus",
    "SE-real",
    "T1map-scanner",
]


def extract_single_volume(
    D: np.ndarray,
    frame_fg_sequence,
    subvol_idx_start: int,
    shape: tuple[int, int, int],
):
    n_frames, n_rows, n_cols = shape
    frame_fg = frame_fg_sequence[subvol_idx_start]

    # Find scaling values (should potentially be inside scaling loop)
    pixel_value_transform = frame_fg.PixelValueTransformationSequence[0]
    slope = float(pixel_value_transform.RescaleSlope)
    intercept = float(pixel_value_transform.RescaleIntercept)
    private = frame_fg[0x2005, 0x140F][0]
    scale_slope = private[0x2005, 0x100E].value

    # Loop over and scale values.
    volume = np.zeros((n_frames, n_rows, n_cols), dtype=np.single)
    for idx in range(n_frames):
        slice_idx = idx + subvol_idx_start
        volume[idx] = (intercept + slope * D[slice_idx]) / (scale_slope * slope)

    # Get the original data shape
    dr, dc = (float(x) for x in frame_fg.PixelMeasuresSequence[0].PixelSpacing)
    plane_orientation = frame_fg.PlaneOrientationSequence[0]
    orientation = np.array(plane_orientation.ImageOrientationPatient)

    # Find orientation of data array relative to LPS-coordinate system.
    row_cosine = orientation[:3]
    col_cosine = orientation[3:]

    # Create DICOM-definition affine map to LPS.
    T_1 = np.array(frame_fg.PlanePositionSequence[0].ImagePositionPatient)
    T_N = np.array(
        frame_fg_sequence[n_frames - 1].PlanePositionSequence[0].ImagePositionPatient
    )

    # Build DICOM-standard affine, change coordinates from LPS to RAS, then
    # reorient data so index number and direction cooresponds to
    # coordinate axis number and direction.
    A_dcm = dicom_standard_afffine(row_cosine, col_cosine, dr, dc, T_N, T_1, n_frames)
    C = change_of_coordinates_map("LPS", "RAS")
    mri = data_reorientation(SimpleMRI(D, C @ A_dcm))

    nii_oriented = nibabel.nifti1.Nifti1Image(mri.data, mri.affine)
    nii_oriented.set_sform(nii_oriented.affine, "scanner")
    nii_oriented.set_qform(nii_oriented.affine, "scanner")
    description = {
        "TR": float(frame_fg.MRTimingAndRelatedParametersSequence[0].RepetitionTime),
        "TE": float(frame_fg.MREchoSequence[0].EffectiveEchoTime),
    }
    if hasattr(frame_fg.MRModifierSequence[0], "InversionTimes"):
        description["TI"] = frame_fg.MRModifierSequence[0].InversionTimes[0]
    return {"nifti": nii_oriented, "descrip": description}


def dcm2nii(dcmpath: Path, subvolumes: list[str]):
    dcm = pydicom.dcmread(dcmpath)
    frames_total = int(dcm.NumberOfFrames)
    n_frames = frames_total // len(VOLUME_LABELS)
    n_rows = dcm.Rows
    n_cols = dcm.Columns
    D = dcm.pixel_array.astype(np.single)
    vols_out = []
    for volname in subvolumes:
        vol_idx = VOLUME_LABELS.index(volname)
        # Find volume slices representing current subvolume
        subvol_idx_start = vol_idx * n_frames
        subvol_idx_end = (vol_idx + 1) * n_frames
        logger.info(
            (
                f"Converting volume {vol_idx+1}/{len(VOLUME_LABELS)}: {volname} between indices"
                + f"{subvol_idx_start, subvol_idx_end} / {frames_total}."
            )
        )
        frame_fg_sequence = dcm.PerFrameFunctionalGroupsSequence
        volume_dict = extract_single_volume(
            D, frame_fg_sequence, subvol_idx_start, (n_frames, n_rows, n_cols)
        )
        vols_out.append(volume_dict)
    return vols_out


def dicom_standard_afffine(
    row_cosine: np.ndarray,
    col_cosine: np.ndarray,
    dr: float,
    dc: float,
    T_N: np.ndarray,
    T_1: np.ndarray,
    n_frames: int,
) -> np.ndarray:
    # Create DICOM-definition affine map to LPS.
    M_dcm = np.zeros((4, 4))
    M_dcm[:3, 0] = row_cosine * dc
    M_dcm[:3, 1] = col_cosine * dr
    M_dcm[:3, 2] = (T_N - T_1) / (n_frames - 1)
    M_dcm[:3, 3] = T_1
    M_dcm[3, 3] = 1.0

    # Reorder from "natural index order" to DICOM affine map definition order.
    N_order = np.eye(4)[[2, 1, 0, 3]]
    return M_dcm @ N_order
