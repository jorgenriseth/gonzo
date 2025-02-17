rule create_lutfile:
  output:
    "mri_processed_data/freesurfer_lut.json"
  shell:
    "python scripts/create_freesurfer_lut.py"


rule recon_all_setup:
  input:
    t1="mri_dataset/{subject}/ses-01/anat/{subject}_ses-01_T1w.nii.gz",
    FLAIR="mri_dataset/{subject}/ses-01/anat/{subject}_ses-01_FLAIR.nii.gz"
  output:
    t1="mri_processed_data/freesurfer/{subject}/mri/orig/001.mgz",
    FLAIR="mri_processed_data/freesurfer/{subject}/mri/orig/FLAIRraw.mgz"
  shell:
    "mri_convert {input.t1} {output.t1} && "
    "mri_convert --no_scale 1 {input.FLAIR} {output.FLAIR}"


rule recon_all_FLAIR:
  input:
    t1="mri_processed_data/freesurfer/{subject}/mri/orig/001.mgz",
    FLAIR="mri_processed_data/freesurfer/{subject}/mri/orig/FLAIRraw.mgz"
  output:
    segmentations=protected(expand(
      "mri_processed_data/freesurfer/{{subject}}/mri/{seg}.mgz",
      seg=["aparc+aseg", "aseg", "wmparc"]
    )),
    surfs=protected(expand(
      "mri_processed_data/freesurfer/{{subject}}/surf/{surf}",
      surf=["lh.pial", "rh.pial", "lh.white", "rh.white"]
    ))
  resources:
    time="48:00:00",
  threads: 8
  shell:
    "recon-all"
    " -sd $(realpath $(dirname {output.segmentations[0]})/../../)"
    " -s {wildcards.subject}"
    # " -FLAIR {input.FLAIR}"
    # " -FLAIRpial"
    " -cm"
    " -parallel"
    " -all"


rule fastsurfer:
    input:
        t1="mri_dataset/{subject}/ses-01/anat/{subject}_ses-01_T1w.nii.gz"
    output:
        segmentations=protected(expand(
            "mri_processed_data/fastsurfer/{{subject}}/mri/{seg}.mgz",
            seg=["aparc+aseg", "aseg", "wmparc"]
        )),
        surfs=protected(expand(
            "mri_processed_data/fastsurfer/{{subject}}/surf/{surf}",
            surf=["lh.pial", "rh.pial", "lh.white", "rh.white"]
        ))
    threads: 10
    shell:
      "/fastsurfer/run_fastsurfer.sh"
      " --fs_license $(realpath singularity/license.txt)"
      " --t1 $(realpath {input.t1})"
      " --sid {wildcards.subject}"
      " --sd $(realpath $(dirname {output[0]})/../..)"
      " --parallel"
      " --3T"
      " --threads {threads}"
      " --no_hypothal"
      " --viewagg_device 'cpu'"
