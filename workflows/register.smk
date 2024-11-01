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


ruleorder: reference_image > reslice_T1w
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
  shell:
    "greedy -d 3"
    " -rf {input.fixed}"
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
  output:
    "mri_processed_data/{subject}/registered/{subject}_{session}_acq-mixed_{T1_variant}_registered.nii.gz",

use rule reslice as reslice_mixed_scanner with:
  input: 
    fixed="mri_processed_data/{subject}/registered/{subject}_ses-01_T1w_registered.nii.gz",
    moving="mri_dataset/{subject}/{session}/mixed/{subject}_{session}_acq-mixed_T1map_scanner.nii.gz",
    transform="mri_processed_data/{subject}/transforms/{subject}_{session}_acq-mixed.mat"
  output:
    "mri_processed_data/{subject}/registered/{subject}_{session}_acq-mixed_T1map_scanner_registered.nii.gz",

# DTI
use rule register as register_dti with:
  input:
    fixed="mri_processed_data/{subject}/registered/{subject}_ses-01_T2w_registered.nii.gz",
    moving="mri_dataset/derivatives/{subject}/ses-01/dti/dtifit_MD.nii.gz"
  params:
    metric="NMI"
  output:
    "mri_processed_data/{subject}/transforms/{subject}_ses-01_DTI.mat"

ruleorder: reslice_4D > reslice_dti
use rule reslice as reslice_dti with:
  input: 
    fixed="mri_processed_data/{subject}/registered/{subject}_ses-01_T1w_registered.nii.gz",
    moving="mri_dataset/derivatives/{subject}/ses-01/dti/dtifit_{dti_value}.nii.gz",
    transform="mri_processed_data/{subject}/transforms/{subject}_ses-01_DTI.mat"
  output:
    "mri_processed_data/{subject}/registered/{subject}_ses-01_dDTI_{dti_value}_registered.nii.gz",


rule reslice_4D:
  input:
    fixed="mri_processed_data/{subject}/registered/{subject}_ses-01_T1w_registered.nii.gz",
    moving="mri_dataset/derivatives/{subject}/ses-01/dti/dtifit_tensor.nii.gz",
    transform="mri_processed_data/{subject}/transforms/{subject}_ses-01_DTI.mat"
  output:
    "mri_processed_data/{subject}/registered/{subject}_ses-01_dDTI_tensor_registered.nii.gz",
  threads: 4
  shell:
    "bash scripts/4d_reslice.sh"
    " {input.fixed}"
    " {input.moving}"
    " {input.transform}"
    " {output}"
    " {threads}"
