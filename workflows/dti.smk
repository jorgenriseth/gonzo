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
    "mri_dataset/derivatives/{subject}/ses-01/dti/{subject}_ses-01_acq-multiband_sense_topup_b0.nii.gz"
  shell:
    "fslmerge -t {output} {input}"

rule generate_acquisition_params_file:
  input:
    "mri_dataset/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_dir-AP_DTI.json",
    "mri_dataset/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_dir-PA_b0.json"
  output:
    "mri_dataset/derivatives/{subject}/ses-01/dti/topup_acq_params.txt"
  shell:
    "for i in {{1..10}}; do "
    " echo 0 -1 0 $(jq '.EstimatedTotalReadoutTime' {input[0]}) >> {output};"
    "done && "
    "echo 0 1 0 $(jq '.EstimatedTotalReadoutTime' {input[1]}) >> {output}"

rule topup:
  input:
    b0="mri_dataset/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_topup_b0.nii.gz",
    acqparams="mri_dataset/derivatives/{subject}/ses-01/dti/topup_acq_params.txt"
  output:
    topup_fieldcoeff="mri_dataset/derivatives/{subject}/ses-01/dti/topup_output_fieldcoef.nii.gz",
    topup_out="mri_dataset/derivatives/{subject}/ses-01/dti/topup_output_movpar.txt",
    unwarped="mri_dataset/derivatives/{subject}/ses-01/dti/topup_b0.nii.gz",
    field="mri_dataset/derivatives/{subject}/ses-01/dti/topup_field.nii.gz"
  shell:
    "topup"
    " --imain={input.b0}"
    " --datain={input.acqparams}"
    " --config=b02b0.cnf"
    " --out=$(echo {output.topup_out} | sed s/_movpar.txt//)"
    " --iout={output.unwarped}"
    " --fout={output.field}"


rule topup_corrected_mean:
  input:
    "mri_dataset/derivatives/{subject}/ses-01/dti/topup_b0.nii.gz",
  output:
    "mri_dataset/derivatives/{subject}/ses-01/dti/mean_topup_b0.nii.gz",
  shell:
    "fslmaths {input} -Tmean {output}"


rule dti_mask:
  input:
    "mri_dataset/derivatives/{subject}/ses-01/dti/mean_topup_b0.nii.gz",
  output:
    "mri_dataset/derivatives/{subject}/ses-01/dti/mean_topup_b0_brain.nii.gz",
    "mri_dataset/derivatives/{subject}/ses-01/dti/mean_topup_b0_brain_mask.nii.gz",
  shell:
    "bet {input} {output[0]} -m -f 0.4"


rule eddy_correction:
  input:
    dti="mri_dataset/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_dir-AP_DTI.nii.gz",
    bvecs="mri_dataset/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_dir-AP_DTI.bvec",
    bvals="mri_dataset/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_dir-AP_DTI.bval",
    topup="mri_dataset/derivatives/{subject}/ses-01/dti/topup_output_movpar.txt",
    mask="mri_dataset/derivatives/{subject}/ses-01/dti/mean_topup_b0_brain_mask.nii.gz",
    acqp="mri_dataset/derivatives/{subject}/ses-01/dti/topup_acq_params.txt",
    index_file="mri_dataset/derivatives/{subject}/ses-01/dti/eddy_index.txt",
  output:
    nii="mri_dataset/derivatives/{subject}/ses-01/dti/eddy_corrected_data.nii.gz",
    bvecs="mri_dataset/derivatives/{subject}/ses-01/dti/eddy_corrected_data.eddy_rotated_bvecs"
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

rule eddy_index_file:
  input:
    "mri_dataset/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_dir-AP_DTI.nii.gz",
  output:
    temp("mri_dataset/derivatives/{subject}/ses-01/dti/eddy_index.txt")
  shell:
    "bash scripts/eddy_index.sh {input} {output}"

rule eddy_corrected_b0:
  input:
    "mri_dataset/derivatives/{subject}/ses-01/dti/eddy_corrected_data.nii.gz"
  output:
    "mri_dataset/derivatives/{subject}/ses-01/dti/eddy_corrected_b0.nii.gz"
  shell:
    "fslroi {input} {output} 150 10"

# TODO: FSL does not like 4D volumes in masking. Should either do mean or first volume extraction
rule eddy_mask:
  input:
    "mri_dataset/derivatives/{subject}/ses-01/dti/eddy_corrected_b0.nii.gz",
  output:
    "mri_dataset/derivatives/{subject}/ses-01/dti/eddy_corrected_b0_brain.nii.gz",
    "mri_dataset/derivatives/{subject}/ses-01/dti/eddy_corrected_b0_brain_mask.nii.gz",
  shell:
    "bet {input} {output[0]} -m -f 0.4"

rule fit_dti_tensor:
  input:
    dti="mri_dataset/derivatives/{subject}/ses-01/dti/eddy_corrected_data.nii.gz",
    bvecs="mri_dataset/derivatives/{subject}/ses-01/dti/eddy_corrected_data.eddy_rotated_bvecs",
    bvals="mri_dataset/{subject}/ses-01/dwi/{subject}_ses-01_acq-multiband_sense_dir-AP_DTI.bval",
    mask="mri_dataset/derivatives/{subject}/ses-01/dti/eddy_corrected_b0_brain_mask.nii.gz",
  output:
    "mri_dataset/derivatives/{subject}/ses-01/dti/dtifit_FA.nii.gz",
    "mri_dataset/derivatives/{subject}/ses-01/dti/dtifit_tensor.nii.gz"
  shell:
    "dtifit"
    " -k {input.dti}"
    " -o $(echo {output[0]} | sed s/_FA.nii.gz//)"
    " -m {input.mask}"
    " -r {input.bvecs}"
    " -b {input.bvals}"
    " --save_tensor"

rule clean_dti:
  input:
    tensor="mri_processed_data/{subject}/registered/sub-01_ses-01_dDTI_tensor_registered.nii.gz",
    mask="mri_processed_data/{subject}/segmentations/sub-01_seg-aparc+aseg_refined.nii.gz"
  output:
    "mri_processed_data/{subject}/dti/{subject}_ses-01_dDTI_cleaned.nii.gz"
  shell:
    "python src/gonzo/clean_dti_data.py"
    " --dti {input.tensor}"
    " --mask {input.mask}"
    " --out {output}"

