#!/bin/bash
set -eou pipefail

zip -rv build-record/mri-dataset.zip \
  $(for ses in ses-0{1..5}; do
    echo mri_dataset/sub-01/${ses}/anat/sub-01_${ses}_T1w{.nii.gz,.json}
    echo mri_dataset/sub-01/${ses}/anat/sub-01_${ses}_acq-looklocker_IRT1{.nii.gz,.json,_trigger_times.txt}
    echo mri_dataset/sub-01/${ses}/mixed/sub-01_${ses}_acq-mixed{_SE-modulus.nii.gz,_T1map_scanner.nii.gz,_IR-corrected-real.nii.gz,.json,_meta.json}
  done) \
  mri_dataset/sub-01/ses-01/anat/sub-01_ses-01_T2w{.nii.gz,.json} \
  mri_dataset/sub-01/ses-01/anat/sub-01_ses-01_FLAIR{.nii.gz,.json} \
  mri_dataset/sub-01/ses-01/dwi/sub-01_ses-01_acq-multiband_sense_dir-AP_DTI{.nii.gz,.bval,.bvec,.json,_ADC.nii.gz} \
  mri_dataset/sub-01/ses-01/dwi/sub-01_ses-01_acq-multiband_sense_dir-PA_b0{.nii.gz,.bval,.bvec,.json} \
  mri_dataset/timetable.tsv \
  mri_dataset/blood_concentrations.csv

zip -rv build-record/mri-dataset-precontrast-only.zip \
  mri_dataset/sub-01/ses-01/anat/sub-01_ses-01_T1w{.nii.gz,.json} \
  mri_dataset/sub-01/ses-01/anat/sub-01_ses-01_acq-looklocker_IRT1{.nii.gz,.json,_trigger_times.txt} \
  mri_dataset/sub-01/ses-01/mixed/sub-01_ses-01_acq-mixed{_SE-modulus.nii.gz,_T1map_scanner.nii.gz,_IR-corrected-real.nii.gz,.json,_meta.json} \
  mri_dataset/sub-01/ses-01/anat/sub-01_ses-01_T2w{.nii.gz,.json} \
  mri_dataset/sub-01/ses-01/anat/sub-01_ses-01_FLAIR{.nii.gz,.json} \
  mri_dataset/sub-01/ses-01/dwi/sub-01_ses-01_acq-multiband_sense_dir-AP_DTI{.nii.gz,.bval,.bvec,.json,_ADC.nii.gz} \
  mri_dataset/sub-01/ses-01/dwi/sub-01_ses-01_acq-multiband_sense_dir-PA_b0{.nii.gz,.bval,.bvec,.json} \
  mri_dataset/timetable.tsv \
  mri_dataset/blood_concentrations.csv

zip -rv build-record/freesurfer.zip \
  mri_processed_data/freesurfer/sub-01/

zip -rv build-record/fastsurfer.zip \
  mri_processed_data/fastsurfer/sub-01/

zip -rv build-record/mri-processed.zip \
  $(for ses in ses-0{1..5}; do
    echo mri_dataset/derivatives/sub-01/${ses}/sub-01_${ses}_acq-looklocker_T1map{.nii.gz,_nICE.nii.gz}
    echo mri_dataset/derivatives/sub-01/${ses}/sub-01_${ses}_acq-mixed_T1map.nii.gz
  done) \
  mri_dataset/derivatives/sub-01/ses-01/dwi/sub-01_ses-01_dDTI_{FA,MD,L{1..3},V{1..3},tensor}.nii.gz \
  mri_processed_data/sub-01/registered/sub-01_ses-0{1..5}_T1w_registered.nii.gz \
  mri_processed_data/sub-01/registered/sub-01_ses-01_T2w_registered.nii.gz \
  mri_processed_data/sub-01/registered/sub-01_ses-0{1..5}_acq-looklocker_T1map_registered.nii.gz \
  mri_processed_data/sub-01/registered/sub-01_ses-0{1..5}_acq-mixed_T1map_registered.nii.gz \
  mri_processed_data/sub-01/registered/sub-01_ses-0{1..5}_acq-mixed_T1map_scanner_registered.nii.gz \
  mri_processed_data/sub-01/transforms/sub-01_ses-0{1..5}_T1w.mat \
  mri_processed_data/sub-01/transforms/sub-01_ses-01_T2w.mat \
  mri_processed_data/sub-01/T1w_normalized/sub-01_ses-0{1..5}_T1w_normalized.nii.gz \
  mri_processed_data/sub-01/transforms/sub-01_ses-0{1..5}_acq-looklocker.mat \
  mri_processed_data/sub-01/transforms/sub-01_ses-0{1..5}_acq-mixed.mat \
  mri_processed_data/sub-01/T1maps/sub-01_ses-0{1..5}_T1map_hybrid.nii.gz \
  mri_processed_data/sub-01/registered/sub-01_ses-01_dDTI_{FA,MD,L{1..3},V{1..3},tensor}_registered.nii.gz \
  mri_processed_data/sub-01/transforms/sub-01_ses-01_dDTI.mat \
  mri_processed_data/sub-01/dwi/sub-01_ses-01_dDTI_cleaned.nii.gz \
  mri_processed_data/sub-01/segmentations/sub-01_seg-csf_binary.nii.gz \
  mri_processed_data/sub-01/segmentations/sub-01_seg-intracranial_binary.nii.gz \
  mri_processed_data/sub-01/segmentations/sub-01_seg-refroi-left-orbital_binary.nii.gz \
  mri_processed_data/sub-01/segmentations/sub-01_seg-aseg_refined.nii.gz \
  mri_processed_data/sub-01/segmentations/sub-01_seg-wmparc_refined.nii.gz \
  mri_processed_data/sub-01/segmentations/sub-01_seg-aparc+aseg_refined.nii.gz \
  mri_processed_data/sub-01/segmentations/sub-01_seg-csf-aseg.nii.gz \
  mri_processed_data/sub-01/segmentations/sub-01_seg-csf-wmparc.nii.gz \
  mri_processed_data/sub-01/segmentations/sub-01_seg-csf-aparc+aseg.nii.gz \
  mri_processed_data/sub-01/concentrations/sub-01_ses-0{1..5}_concentration.nii.gz

zip -rv build-record/surfaces.zip \
  mri_processed_data/sub-01/modeling/surfaces/{rh,lh}_pial.stl \
  mri_processed_data/sub-01/modeling/surfaces/white.stl \
  mri_processed_data/sub-01/modeling/surfaces/ventricles.stl \
  mri_processed_data/sub-01/modeling/surfaces/subcortical_gm.stl

zip -rv build-record/mesh-data.zip \
  mri_processed_data/sub-01/modeling/resolution32/data.vtu \
  mri_processed_data/sub-01/modeling/resolution32/data.vtk \
  mri_processed_data/sub-01/modeling/resolution32/data.hdf \
  mri_processed_data/sub-01/modeling/resolution32/mesh_xdmfs/{mesh,subdomains,boundaries}.{xdmf,h5}
