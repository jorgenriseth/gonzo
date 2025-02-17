rule register_all:
  input:
    T1w=[
        f"mri_processed_data/{subject}/registered/{subject}_{session}_T1w_registered.nii.gz"
        for subject in SUBJECTS
        for session in SESSIONS[subject]
    ],
    T1map_LL=[
        f"mri_processed_data/{subject}/registered/{subject}_{session}_acq-looklocker_T1map_registered.nii.gz"
        for subject in SUBJECTS
        for session in SESSIONS[subject]
    ],
    T1map_mixed=[
        f"mri_processed_data/{subject}/registered/{subject}_{session}_acq-mixed_{variant}_registered.nii.gz"
        for subject in SUBJECTS
        for session in SESSIONS[subject]
        for variant in ["T1map", "T1map_raw", "R1map", "R1map_raw", "T1map_scanner", "R1map_scanner"]
    ],
    DTI=[
        f"mri_processed_data/{subject}/registered/{subject}_ses-01_dDTI_{variant}_registered.nii.gz"
        for subject in SUBJECTS
        for variant in ["MD", "FA"]
    ]


rule reference_image:
  input:
    "mri_dataset/{subject}/ses-01/anat/{subject}_ses-01_T1w.nii.gz"
  output:
    "mri_processed_data/{subject}/registered/{subject}_ses-01_T1w_registered.nii.gz"
  shell:
    "cp {input} {output}"


rule register:
  threads: 10  # Use extra threads to avoid memory overload from parallell jobs
  params:
    metric="NCC 5x5x5"
  shell:
    "greedy -d 3 -a" 
    " -i {input.fixed} {input.moving}"
    " -o {output}"
    " -ia-image-centers"
    " -dof 6"
    " -m {params.metric}"
    " -threads {threads}"


rule reslice:
  threads: 4
  params:
    interp_mode="NN"
  shell:
    "greedy -d 3"
    " -rf {input.fixed}"
    " -ri {params.interp_mode}"
    " -rm {input.moving} {output}"
    " -r {input.transform}"
    " -threads {threads}"


# T1w
use rule register as register_T1w with:
  input:
    fixed="mri_processed_data/{subject}/registered/{subject}_ses-01_T1w_registered.nii.gz",
    moving="mri_dataset/{subject}/{session}/anat/{subject}_{session}_T1w.nii.gz"
  output:
    "mri_processed_data/{subject}/transforms/{subject}_{session}_T1w.mat"


use rule reslice as reslice_T1w with:
  input:
    fixed="mri_processed_data/{subject}/registered/{subject}_ses-01_T1w_registered.nii.gz",
    moving="mri_dataset/{subject}/{session}/anat/{subject}_{session}_T1w.nii.gz",
    transform="mri_processed_data/{subject}/transforms/{subject}_{session}_T1w.mat"
  output:
    "mri_processed_data/{subject}/registered/{subject}_{session}_T1w_registered.nii.gz",


# FLAIR
use rule register as register_FLAIR with:
  input:
    fixed="mri_processed_data/{subject}/registered/{subject}_ses-01_FLAIR_registered.nii.gz",
    moving="mri_dataset/{subject}/{session}/anat/{subject}_{session}_FLAIR.nii.gz"
  output:
    "mri_processed_data/{subject}/transforms/{subject}_{session}_FLAIR.mat"


use rule reslice as reslice_FLAIR with:
  input:
    fixed="mri_processed_data/{subject}/registered/{subject}_ses-01_FLAIR_registered.nii.gz",
    moving="mri_dataset/{subject}/{session}/anat/{subject}_{session}_FLAIR.nii.gz",
    transform="mri_processed_data/{subject}/transforms/{subject}_{session}_FLAIR.mat"
  output:
    "mri_processed_data/{subject}/registered/{subject}_{session}_FLAIR_registered.nii.gz",


# T2w
use rule register as register_T2w with:
  input:
    fixed="mri_processed_data/{subject}/registered/{subject}_ses-01_T1w_registered.nii.gz",
    moving="mri_dataset/{subject}/ses-01/anat/{subject}_ses-01_T2w.nii.gz"
  params:
    metric="NMI"
  output:
    "mri_processed_data/{subject}/transforms/{subject}_{session}_T2w.mat"


use rule reslice as reslice_T2w with:
  input:
    fixed="mri_processed_data/{subject}/registered/{subject}_ses-01_T1w_registered.nii.gz",
    moving="mri_dataset/{subject}/ses-01/anat/{subject}_ses-01_T2w.nii.gz",
    transform="mri_processed_data/{subject}/transforms/{subject}_{session}_T2w.mat"
  output:
    "mri_processed_data/{subject}/registered/{subject}_{session}_T2w_registered.nii.gz",


# LL
use rule register as register_T1map_LL with:
  input:
    fixed="mri_processed_data/{subject}/registered/{subject}_ses-01_T1w_registered.nii.gz",
    moving="mri_dataset/derivatives/{subject}/{session}/{subject}_{session}_acq-looklocker_R1map.nii.gz"
  output:
    transform="mri_processed_data/{subject}/transforms/{subject}_{session}_acq-looklocker.mat"


use rule reslice as reslice_T1map_LL with:
  input:
    fixed="mri_processed_data/{subject}/registered/{subject}_ses-01_T1w_registered.nii.gz",
    moving="mri_dataset/derivatives/{subject}/{session}/{subject}_{session}_acq-looklocker_{T1_variant}.nii.gz",
    transform="mri_processed_data/{subject}/transforms/{subject}_{session}_acq-looklocker.mat",
  output:
    "mri_processed_data/{subject}/registered/{subject}_{session}_acq-looklocker_{T1_variant}_registered.nii.gz",

# Mixed
use rule register as register_mixed with:
  input:
    fixed="mri_processed_data/{subject}/registered/{subject}_ses-01_T2w_registered.nii.gz",
    moving="mri_dataset/{subject}/{session}/mixed/{subject}_{session}_acq-mixed_SE-modulus.nii.gz"
  output:
    "mri_processed_data/{subject}/transforms/{subject}_{session}_acq-mixed.mat"


use rule reslice as reslice_mixed with:
  input: 
    fixed="mri_processed_data/{subject}/registered/{subject}_ses-01_T1w_registered.nii.gz",
    moving="mri_dataset/derivatives/{subject}/{session}/{subject}_{session}_acq-mixed_{T1_variant}.nii.gz",
    transform="mri_processed_data/{subject}/transforms/{subject}_{session}_acq-mixed.mat"
  params:
    interp_mode="NN"
  output:
    "mri_processed_data/{subject}/registered/{subject}_{session}_acq-mixed_{T1_variant}_registered.nii.gz",

use rule reslice as reslice_mixed_scanner with:
  input: 
    fixed="mri_processed_data/{subject}/registered/{subject}_ses-01_T1w_registered.nii.gz",
    moving="mri_dataset/{subject}/{session}/mixed/{subject}_{session}_acq-mixed_T1map_scanner.nii.gz",
    transform="mri_processed_data/{subject}/transforms/{subject}_{session}_acq-mixed.mat"
  params:
    interp_mode="NN"
  output:
    "mri_processed_data/{subject}/registered/{subject}_{session}_acq-mixed_T1map_scanner_registered.nii.gz",

# DTI
use rule register as register_dti with:
  input:
    fixed="mri_processed_data/{subject}/registered/{subject}_ses-01_T2w_registered.nii.gz",
    moving="mri_dataset/derivatives/{subject}/ses-01/dwi/{subject}_ses-01_dDTI_MD.nii.gz"
  params:
    metric="NMI"
  output:
    "mri_processed_data/{subject}/transforms/{subject}_ses-01_dDTI.mat"

rule reslice_dti:
  input:
    fixed="mri_processed_data/{subject}/registered/{subject}_ses-01_T1w_registered.nii.gz",
    moving="mri_dataset/derivatives/{subject}/ses-01/dwi/{subject}_ses-01_dDTI_MD.nii.gz",
    transform="mri_processed_data/{subject}/transforms/{subject}_ses-01_dDTI.mat"
  output:
    "mri_processed_data/{subject}/registered/{subject}_ses-01_dDTI_tensor_registered.nii.gz",
    "mri_processed_data/{subject}/registered/{subject}_ses-01_dDTI_MD_registered.nii.gz",
    "mri_processed_data/{subject}/registered/{subject}_ses-01_dDTI_FA_registered.nii.gz",
    [f"mri_processed_data/{{subject}}/registered/{{subject}}_ses-01_dDTI_V{idx}_registered.nii.gz" for idx in range(1, 4)],
    [f"mri_processed_data/{{subject}}/registered/{{subject}}_ses-01_dDTI_L{idx}_registered.nii.gz" for idx in range(1, 4)],
  threads: 4
  shell:
      "gmri2fem dti reslice-dti"
      " --fixed {input.fixed}"
      " --dtidir $(dirname {input.moving})"
      " --prefix_pattern $(basename {input.transform} | sed s/.mat//)"
      " --outdir $(dirname {output[0]})"
      " --transform {input.transform}"
      " --threads {threads}"
      " --suffix _registered"
      " --greedyargs '-ri NN'"
