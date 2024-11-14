rule extract_dynamic_b0:
  input:
    "mri_dataset/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_dir-AP_DTI.nii.gz"
  output:
    "mri_dataset/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_dir-AP_b0.nii.gz"
  shell:
    "fslroi {input} {output} 150 10"

rule merge_b0_with_prescan:
  input:
    "mri_dataset/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_dir-AP_b0.nii.gz",
    "mri_dataset/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_dir-PA_b0.nii.gz"
  output:
    temp("mri_dataset/derivatives/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_topup_b0.nii.gz")
  shell:
    "fslmerge -t {output} {input}"

rule generate_acquisition_params_file:
  input:
    "mri_dataset/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_dir-AP_DTI.nii.gz",
    "mri_dataset/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_dir-PA_b0.json"
  output:
    temp("mri_dataset/derivatives/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_topup_acq_params.txt")
  shell:
    "gmri2fem dti topup-params"
    " --imain {input[0]}"
    " --b0_topup {input[1]}"
    " --output {output}"

rule topup_correct:
  input:
    b0="mri_dataset/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_topup_b0.nii.gz",
    acqparams="mri_dataset/derivatives/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_topup_acq_params.txt"
  output:
    topup_fieldcoeff="mri_dataset/derivatives/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_topup_output_fieldcoef.nii.gz",
    topup_out="mri_dataset/derivatives/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_topup_output_movpar.txt",
    unwarped="mri_dataset/derivatives/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_topup_output_b0.nii.gz",
    unwarped_mean="mri_dataset/derivatives/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_topup_output_b0_mean.nii.gz",
    field="mri_dataset/derivatives/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_topup_output_field.nii.gz"
  shell:
    "topup"
    " --imain={input.b0}"
    " --datain={input.acqparams}"
    " --config=b02b0.cnf"
    " --out=$(echo {output.topup_out} | sed s/_movpar.txt//)"
    " --iout=$(echo {output.unwarped} | sed s/.nii.gz//)"
    " --fout={output.field}"


rule mask_topup_corrected_dti:
  input:
    "mri_dataset/derivatives/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_topup_output_b0_mean.nii.gz",
  output:
    temp("mri_dataset/derivatives/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_topup_output_b0_mean_brain_mask.nii.gz"),
  shell:
    "bet {input} $(echo {output} | sed s/_mask.nii.gz//) -m -f 0.2 -n"


rule generate_eddy_index_file:
  input:
    "mri_dataset/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_dir-AP_DTI.nii.gz"
  output:
    temp("mri_dataset/derivatives/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_eddy_index.txt")
  shell:
    "gmri2fem dti eddy-index --input {input} --output {output}"


rule eddy_correct:
  input:
    dti="mri_dataset/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_dir-AP_DTI.nii.gz",
    bvecs="mri_dataset/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_dir-AP_DTI.bvec",
    bvals="mri_dataset/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_dir-AP_DTI.bval",
    topup="mri_dataset/derivatives/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_topup_output_movpar.txt",
    mask="mri_dataset/derivatives/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_topup_output_b0_mean_brain_mask.nii.gz",
    acqp="mri_dataset/derivatives/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_topup_acq_params.txt",
    index_file="mri_dataset/derivatives/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_eddy_index.txt",
  output:
    nii="mri_dataset/derivatives/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_eddy_corrected_data.nii.gz",
    bvecs="mri_dataset/derivatives/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_eddy_corrected_data.eddy_rotated_bvecs"
  params:
    multiband_factor=3
  shell:
    "eddy diffusion"
    " --imain={input.dti}"
    " --mask={input.mask}"
    " --acqp={input.acqp}"
    " --index={input.index_file}"
    " --bvecs={input.bvecs}"
    " --bvals={input.bvals}"
    " --topup=$(echo {input.topup} | sed s/_movpar.txt//)"
    " --out=$(echo {output.nii} | sed s/.nii.gz//)"
    " --ol_type=both"
    " --mb={params.multiband_factor}"


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
    "mri_processed_data/{subject}/dwi/{subject}_ses-01_acq-multiband_sense_{subject}_ses-01_dDTI_cleaned.nii.gz"
  shell:
    "gmri2fem dti clean"
    " --dti {input.tensor}"
    " --mask {input.mask}"
    " --output {output}"
