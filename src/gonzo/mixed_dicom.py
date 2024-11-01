import nibabel
import pydicom
import numpy as np
from pathlib import Path
from loguru import logger

from simple_mri import data_reorientation, change_of_coordinates_map, SimpleMRI

VOLUME_LABELS = [
    "IR-modulus",
    "IR-real",
    "IR-corrected-real",
    "SE-modulus",
    "SE-real",
    "T1map-scanner",
]


def dcm2nii_mixed(dcmpath: Path, subvolumes: list[str]):
    dcm = pydicom.dcmread(dcmpath)
    frames_total = int(dcm.NumberOfFrames)
    num_volume_frames = dcm[0x2001, 0x1018].value  # [Number of Slices MR]
    D = dcm.pixel_array.astype(np.single)
    frame_fg_sequence = dcm.PerFrameFunctionalGroupsSequence

    vols_out = []
    for volname in subvolumes:
        vol_idx = VOLUME_LABELS.index(volname)

        # Find volume slices representing current subvolume
        subvol_idx_start = vol_idx * num_volume_frames
        subvol_idx_end = (vol_idx + 1) * num_volume_frames
        frame_fg = frame_fg_sequence[subvol_idx_start]
        logger.info(
            (
                f"Converting volume {vol_idx+1}/{len(VOLUME_LABELS)}: {volname} between indices"
                + f"{subvol_idx_start, subvol_idx_end} / {frames_total}."
            )
        )
        mri = extract_single_volume(D[subvol_idx_start:subvol_idx_end], frame_fg)

        nii_oriented = nibabel.nifti1.Nifti1Image(mri.data, mri.affine)
        nii_oriented.set_sform(nii_oriented.affine, "scanner")
        nii_oriented.set_qform(nii_oriented.affine, "scanner")

        # Include meta-data
        description = {
            "TR": float(
                frame_fg.MRTimingAndRelatedParametersSequence[0].RepetitionTime
            ),
            "TE": float(frame_fg.MREchoSequence[0].EffectiveEchoTime),
        }
        if hasattr(frame_fg.MRModifierSequence[0], "InversionTimes"):
            description["TI"] = frame_fg.MRModifierSequence[0].InversionTimes[0]
        vols_out.append({"nifti": nii_oriented, "descrip": description})
    return vols_out


def repetition_time(shared_fg: pydicom.Dataset, frame_fg: pydicom.Dataset) -> float:
    if hasattr(frame_fg, "MRTimingAndRelatedParametersSequence"):
        return shared_fg.MRTimingAndRelatedParametersSequence[0].RepetitionTime
    elif hasattr(shared_fg, "MRTimingAndRelatedParametersSequence"):
        return shared_fg.MRTimingAndRelatedParametersSequence[0].RepetitionTime
    raise ValueError("Can't find repetition time in shared or frame functional groups")


def extract_all_volumes(dcmpath: Path):
    dcm = pydicom.dcmread(dcmpath)
    frames_total = int(dcm.NumberOfFrames)
    frames_per_volume = dcm[0x2001, 0x1018].value  # [Number of Slices MR]
    num_volumes = frames_total // frames_per_volume
    assert (
        num_volumes * frames_per_volume == frames_total
    ), "Subvolume dimensions do not match"

    D = dcm.pixel_array.astype(np.single)
    shared_fg = dcm.PerFrameFunctionalGroupsSequence
    frame_fg_sequence = dcm.PerFrameFunctionalGroupsSequence

    vols_out = []
    for vol_idx in range(num_volumes):
        # Find volume slices representing current subvolume
        subvol_idx_start = vol_idx * frames_per_volume
        subvol_idx_end = (vol_idx + 1) * frames_per_volume
        frame_fg = frame_fg_sequence[subvol_idx_start]
        mri = extract_single_volume(
            D[subvol_idx_start:subvol_idx_end],
            frame_fg_sequence[subvol_idx_start:subvol_idx_end],
        )

        nii = nibabel.nifti1.Nifti1Image(mri.data, mri.affine)
        nii.set_sform(nii.affine, "scanner")
        nii.set_qform(nii.affine, "scanner")

        nii.header["pixdim"][4] = repetition_time(shared_fg, frame_fg)

        # Include meta-data
        description = {
            "TE": float(frame_fg.MREchoSequence[0].EffectiveEchoTime),
        }
        if hasattr(frame_fg.MRModifierSequence[0], "InversionTimes"):
            description["TI"] = frame_fg.MRModifierSequence[0].InversionTimes[0]

    return vols_out


def extract_single_volume(
    D: np.ndarray,
    frame_fg: pydicom.Dataset,
) -> SimpleMRI:
    # Find scaling values (should potentially be inside scaling loop)
    pixel_value_transform = frame_fg.PixelValueTransformationSequence[0]
    slope = float(pixel_value_transform.RescaleSlope)
    intercept = float(pixel_value_transform.RescaleIntercept)
    private = frame_fg[0x2005, 0x140F][0]
    scale_slope = private[0x2005, 0x100E].value

    # Loop over and scale values.
    # TODO: Change/Choose correct dtype for this volume
    volume = np.zeros_like(D, dtype=np.single)
    for idx in range(D.shape[0]):
        volume[idx] = (intercept + slope * D[idx]) / (scale_slope * slope)

    A_dcm = dicom_standard_affine(frame_fg)
    C = change_of_coordinates_map("LPS", "RAS")
    mri = data_reorientation(SimpleMRI(volume, C @ A_dcm))

    return mri


def dicom_standard_affine(
    frame_fg: pydicom.Dataset,
) -> np.ndarray:
    # Get the original data shape
    df = float(frame_fg.PixelMeasuresSequence[0].SpacingBetweenSlices)
    dr, dc = (float(x) for x in frame_fg.PixelMeasuresSequence[0].PixelSpacing)
    plane_orientation = frame_fg.PlaneOrientationSequence[0]
    orientation = np.array(plane_orientation.ImageOrientationPatient)

    # Find orientation of data array relative to LPS-coordinate system.
    row_cosine = orientation[:3]
    col_cosine = orientation[3:]
    frame_cosine = np.cross(row_cosine, col_cosine)

    # Create DICOM-definition affine map to LPS.
    T_1 = np.array(frame_fg.PlanePositionSequence[0].ImagePositionPatient)

    # Create DICOM-definition affine map to LPS.
    M_dcm = np.zeros((4, 4))
    M_dcm[:3, 0] = row_cosine * dc
    M_dcm[:3, 1] = col_cosine * dr
    M_dcm[:3, 2] = frame_cosine * df
    M_dcm[:3, 3] = T_1
    M_dcm[3, 3] = 1.0

    # Reorder from "natural index order" to DICOM affine map definition order.
    N_order = np.eye(4)[[2, 1, 0, 3]]
    return M_dcm @ N_order
