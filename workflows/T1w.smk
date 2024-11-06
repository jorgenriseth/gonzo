rule T1w_signal_intensity_increase:
  input:
    reference="mri_processed_data/{subject}/T1w_normalized/{subject}_ses-01_T1w_normalized.nii.gz",
    image="mri_processed_data/{subject}/T1w_normalized/{subject}_{session}_T1w_normalized.nii.gz",
    mask="mri_processed_data/{subject}/segmentations/{subject}_seg-intracranial_binary.nii.gz",
  output:
    "mri_processed_data/{subject}/T1w_signal_difference/{subject}_{session}_T1w_signal-difference.nii.gz",
  shell:
    "gmri2fem mri t1w-sigdiff"
    " --input {input.image}"
    " --reference {input.reference}"
    " --mask {input.mask}"
    " --output {output}"


rule normalize_T1w:
    input:
        image="mri_processed_data/{subject}/registered/{subject}_{session}_T1w_registered.nii.gz",
        refroi="mri_processed_data/{subject}/segmentations/{subject}_seg-refroi-left-orbital_binary.nii.gz",
    output:
        "mri_processed_data/{subject}/T1w_normalized/{subject}_{session}_T1w_normalized.nii.gz"
    shell:
        "gmri2fem mri t1w-normalize"
        " --input {input.image}"
        " --refroi {input.refroi}"
        " --output {output}"
