rule segment_refinements:
  input:
    reference="mri_processed_data/{subject}/registered/{subject}_ses-01_T1w_registered.nii.gz",
    segmentation=f"{FS_DIR}/{{subject}}/mri/{{seg}}.mgz",
    csfmask="mri_processed_data/{subject}/segmentations/{subject}_seg-csf_binary.nii.gz",
  output:
    refined="mri_processed_data/{subject}/segmentations/{subject}_seg-{seg}_refined.nii.gz",
    csf_segmentation="mri_processed_data/{subject}/segmentations/{subject}_seg-csf-{seg}.nii.gz",
  params:
    label_smoothing = 1.0
  threads: 6
  shell:
    "gmri2fem seg refine"
    " --fs_seg {input.segmentation}"
    " --reference {input.reference}"
    " --csfmask {input.csfmask}"
    " --output_seg {output.refined}"
    " --output_csfseg {output.csf_segmentation}"
    " --label_smoothing {params.label_smoothing}"

rule intracranial_mask:
  input:
    csf="mri_processed_data/{subject}/segmentations/{subject}_seg-csf-aseg.nii.gz",
    brain="mri_processed_data/{subject}/segmentations/{subject}_seg-wmparc_refined.nii.gz",
  output:
    "mri_processed_data/{subject}/segmentations/{subject}_seg-intracranial_binary.nii.gz",
  shell:
    "gmri2fem seg mask-intracranial"
    " --csfmask {input.csf}"
    " --brain_seg {input.brain}"
    " --output {output}"

rule csfmask:
  input:
    "mri_processed_data/{subject}/registered/{subject}_ses-01_T2w_registered.nii.gz",
  output:
    "mri_processed_data/{subject}/segmentations/{subject}_seg-csf_binary.nii.gz",
  shell:
    "gmri2fem seg mask-csf --input {input} --output {output}"


rule orbital_refroi:
  input: 
    T1w = lambda wc: [
      f"mri_processed_data/{{subject}}/registered/{{subject}}_{session}_T1w_registered.nii.gz"
      for session in SESSIONS[wc.subject]
    ],
    segmentation= f"{FS_DIR}/{{subject}}/mri/aparc+aseg.mgz"
  output:
    "mri_processed_data/{subject}/segmentations/{subject}_seg-refroi-left-orbital_binary.nii.gz",
    "mri_processed_data/{subject}/segmentations/{subject}_seg-refroi-right-orbital_binary.nii.gz",
  params: inputdir = lambda wc: f"mri_processed_data/{wc.subject}/registered"
  shell:
    "gmri2fem seg orbital-refroi"
    " --T1w_dir '{params.inputdir}'"
    " --segmentation '{input.segmentation}'"
    " --output '{output[0]}'"
    " --side \"left\" && "
    "gmri2fem seg orbital-refroi"
    " --T1w_dir {params.inputdir}"
    " --segmentation {input.segmentation}"
    " --output {output[1]}"
    " --side \"right\""

rule extended_fs:
  input:
    aparc="mri_processed_data/{subject}/segmentations/{subject}_seg-aparc+aseg_refined.nii.gz",
    wmparc="mri_processed_data/{subject}/segmentations/{subject}_seg-wmparc_refined.nii.gz",
    t2w="mri_processed_data/{subject}/registered/{subject}_ses-01_T2w_registered.nii.gz",
  output:
    "mri_processed_data/{subject}/segmentations/{subject}_seg-extended-fs.nii.gz"
  shell:
    "gmri2fem seg extended-fs"
    " --aparc {input.aparc}"
    " --t2w {input.t2w}"
    " --wmparc {input.wmparc}"
    " --output {output}"


