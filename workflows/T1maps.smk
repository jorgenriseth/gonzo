rule T1maps_all:
  input:
    hybrid_T1maps=[
      f"mri_processed_data/{subject}/T1maps/{subject}_{session}_T1map_hybrid.nii.gz"
      for subject in SUBJECTS
      for session in SESSIONS[subject]
    ],
    registered=[
      f"mri_processed_data/{subject}/registered/{subject}_{session}_{T1_variant}_registered.nii.gz"
      for subject in SUBJECTS
      for session in SESSIONS[subject]
      for T1_variant in ["acq-looklocker_R1map", "acq-looklocker_R1map_raw", "acq-mixed_R1map", "acq-mixed_R1map_raw"]
    ]

rule T1map_estimation:
  input:
    LL=expand(
      "mri_dataset/derivatives/{subject}/{session}/{subject}_{session}_acq-looklocker_T1map.nii.gz",
      subject="sub-01",
      session=[f"ses-{idx:02d}" for idx in range(1, 6)]
    ),
    mixed=expand(
      "mri_dataset/derivatives/{subject}/{session}/{subject}_{session}_acq-mixed_T1map.nii.gz",
      subject="sub-01",
      session=[f"ses-{idx:02d}" for idx in range(1, 6)]
    ),
    LL_R1=expand(
      "mri_dataset/derivatives/{subject}/{session}/{subject}_{session}_acq-looklocker_R1map.nii.gz",
      subject="sub-01",
      session=[f"ses-{idx:02d}" for idx in range(1, 6)]
    ),
    mixed_R1=expand(
      "mri_dataset/derivatives/{subject}/{session}/{subject}_{session}_acq-mixed_R1map.nii.gz",
      subject="sub-01",
      session=[f"ses-{idx:02d}" for idx in range(1, 6)]
    ),

rule T1map_estimation_from_LL:
  input:
    LL="mri_dataset/{subject}/{session}/anat/{subject}_{session}_acq-looklocker_IRT1.nii.gz",
    timestamps="mri_dataset/{subject}/{session}/anat/{subject}_{session}_acq-looklocker_IRT1_trigger_times.txt"
  output:
    T1raw="mri_dataset/derivatives/{subject}/{session}/{subject}_{session}_acq-looklocker_T1map_raw.nii.gz",
  shell:
    "gmri2fem mri looklocker-t1map"
      " --input {input.LL}"
      " --timestamps {input.timestamps}"
      " --output {output.T1raw}"


rule T1map_LL_postprocessing:
  input:
    LL="mri_dataset/{subject}/{session}/anat/{subject}_{session}_acq-looklocker_IRT1.nii.gz",
    T1="mri_dataset/derivatives/{subject}/{session}/{subject}_{session}_acq-looklocker_T1map_raw.nii.gz",
  output:
    "mri_dataset/derivatives/{subject}/{session}/{subject}_{session}_acq-looklocker_T1map.nii.gz",
  params:
    T1_low=100,
    T1_high=6000
  shell:
    "gmri2fem mri looklocker-t1-postprocessing"
    " --LL {input.LL}"
    " --T1map {input.T1}"
    " --output {output}"
    " --T1_low {params.T1_low}"
    " --T1_high {params.T1_high}"


rule T1map_estimation_from_mixed:
  input:
    SE="mri_dataset/{subject}/{session}/mixed/{subject}_{session}_acq-mixed_SE-modulus.nii.gz",
    IR="mri_dataset/{subject}/{session}/mixed/{subject}_{session}_acq-mixed_IR-corrected-real.nii.gz",
    meta="mri_dataset/{subject}/{session}/mixed/{subject}_{session}_acq-mixed_meta.json"
  output:
    T1map="mri_dataset/derivatives/{subject}/{session}/{subject}_{session}_acq-mixed_T1map_raw.nii.gz",
    T1map_post="mri_dataset/derivatives/{subject}/{session}/{subject}_{session}_acq-mixed_T1map.nii.gz",
  params:
    T1_low=100,
    T1_high=10000,
  shell:
    "gmri2fem mri mixed-t1map"
      " --SE {input.SE}"
      " --IR {input.IR}"
      " --meta {input.meta}"
      " --output {output.T1map}"
      " --t1_low {params.T1_low}"
      " --t1_high {params.T1_high}"
      " --postprocessed {output.T1map_post}"


rule hybrid_T1maps:
  input:
    ll="mri_processed_data/{subject}/registered/{subject}_{session}_acq-looklocker_T1map_registered.nii.gz",
    mixed="mri_processed_data/{subject}/registered/{subject}_{session}_acq-mixed_T1map_registered.nii.gz",
    csfmask="mri_processed_data/{subject}/segmentations/{subject}_seg-csf_binary.nii.gz",
  output:
    T1map="mri_processed_data/{subject}/T1maps/{subject}_{session}_T1map_hybrid.nii.gz",
  shell:
    "gmri2fem mri hybrid-t1map"
      " --ll {input.ll}"
      " --mixed {input.mixed}"
      " --csfmask {input.csfmask}"
      " --output {output}"


ruleorder: T1_to_R1 > reslice_T1map_LL > reslice_mixed
rule T1_to_R1:
  input:
    "{anyprefix}T1map{anysuffix}"
  output:
    "{anyprefix}R1map{anysuffix}"
  params:
    t1_low=200,
    t1_high=10000
  shell:
    "gmri2fem mri t1-to-r1 --input {input} --output {output} --T1_low {params.t1_low} --T1_high {params.t1_high}"
