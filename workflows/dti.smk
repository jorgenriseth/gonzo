rule topup:
  input:
    dti="mri_dataset/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_dir-AP_DTI.nii.gz",
    topup="mri_dataset/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_dir-PA_b0.nii.gz"
  output:
    mean_b0="mri_dataset/derivatives/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_topup_output_b0_mean.nii.gz",
    movpar="mri_dataset/derivatives/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_topup_output_movpar.txt",
    acqparams="mri_dataset/derivatives/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_topup_acq_params.txt",
  shell:
    "gmri2fem dti topup"
    " -i {input.dti}"
    " -t {input.topup}"
    " -o $(dirname {output.movpar})"


rule eddy_correct:
  input:
    dti="mri_dataset/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_dir-AP_DTI.nii.gz",
    topup="mri_dataset/derivatives/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_topup_output_b0_mean.nii.gz",
    acq_params="mri_dataset/derivatives/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_topup_acq_params.txt",
  output:
    nii="mri_dataset/derivatives/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_eddy_corrected_data.nii.gz",
    bvecs="mri_dataset/derivatives/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_eddy_corrected_data.eddy_rotated_bvecs"
  params:
    multiband_factor=3
  shell:
    "gmri2fem dti eddy"
    " -i {input.dti}"
    " -t {input.topup}"
    " -a {input.acq_params}"
    " -o {output.nii}"
    " --mb {params.multiband_factor}"
    " --tmppath $HOME/dtitest"

rule extract_eddy_corrected_b0:
  input:
    "mri_dataset/derivatives/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_eddy_corrected_data.nii.gz"
  output:
    temp("mri_dataset/derivatives/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_eddy_corrected_b0.nii.gz")
  shell:
    "fslroi {input} {output} 150 10"


rule compute_eddy_corrected_b0_mean:
  input:
    "mri_dataset/derivatives/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_eddy_corrected_b0.nii.gz"
  output:
    temp("mri_dataset/derivatives/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_eddy_corrected_b0_mean.nii.gz"),
  shell:
    "fslmaths {input} -Tmean {output}"


# TODO: FSL does not like 4D volumes in masking. Should either do mean or first volume extraction
rule mask_eddy_corrected:
  input:
    "mri_dataset/derivatives/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_eddy_corrected_b0_mean.nii.gz",
  output:
    "mri_dataset/derivatives/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_eddy_corrected_b0_mean_brain_mask.nii.gz",
  shell:
    "bet {input} $(echo {output} | sed s/_mask.nii.gz//) -m -f 0.4 -n"


rule fit_dti_tensor:
  input:
    dti="mri_dataset/derivatives/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_eddy_corrected_data.nii.gz",
    bvecs="mri_dataset/derivatives/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_eddy_corrected_data.eddy_rotated_bvecs",
    bvals="mri_dataset/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_dir-AP_DTI.bval",
    mask="mri_dataset/derivatives/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_eddy_corrected_b0_mean_brain_mask.nii.gz",
  output:
    "mri_dataset/derivatives/{subject}/ses-01/dwi/{subject}_ses-01_dDTI_MD.nii.gz",
    "mri_dataset/derivatives/{subject}/ses-01/dwi/{subject}_ses-01_dDTI_FA.nii.gz",
    "mri_dataset/derivatives/{subject}/ses-01/dwi/{subject}_ses-01_dDTI_tensor.nii.gz"
  shell:
    "dtifit"
    " -k {input.dti}"
    " -o $(echo {output[0]} | sed s/_MD.nii.gz//)"
    " -m {input.mask}"
    " -r {input.bvecs}"
    " -b {input.bvals}"
    " --save_tensor"

rule clean_dti:
  input:
    tensor="mri_processed_data/{subject}/registered/{subject}_ses-01_dDTI_tensor_registered.nii.gz",
    mask="mri_processed_data/{subject}/segmentations/{subject}_seg-aparc+aseg_refined.nii.gz"
  output:
    "mri_processed_data/{subject}/dwi/{subject}_ses-01_dDTI_cleaned.nii.gz"
  shell:
    "gmri2fem dti clean"
    " --dti {input.tensor}"
    " --mask {input.mask}"
    " --output {output}"
