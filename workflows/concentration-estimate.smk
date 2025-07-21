rule concentration_estimate:
  input:
    image="mri_processed_data/{subject}/T1maps/{subject}_{session}_T1map_hybrid.nii.gz",
    reference="mri_processed_data/{subject}/T1maps/{subject}_ses-01_T1map_hybrid.nii.gz",
    mask="mri_processed_data/{subject}/segmentations/{subject}_seg-intracranial_binary.nii.gz"
  output:
    "mri_processed_data/{subject}/concentrations/{subject}_{session}_concentration.nii.gz"
  params:
    r1=0.0032
  shell:
    "gmri2fem mri concentration"
    " --input {input.image}"
    " --reference {input.reference}"
    " --output {output}"
    " --r1 {params.r1}"
    " --mask {input.mask}"
