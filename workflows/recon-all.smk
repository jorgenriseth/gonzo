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
    container: None
    params: subject_dir = lambda wc: f"mri_processed_data/fastsurfer/{wc.subject}"
    threads: 12
    shell:
      "python scripts/fastsurfer.py"
      " -t1 {input.t1} "
      " -o {params.subject_dir}"
      " -l docker/license.txt "
      " --threads {threads}"

rule recon_all:
  input:
    t1="mri_dataset/{subject}/ses-01/anat/{subject}_ses-01_T1w.nii.gz",
    flair="mri_dataset/{subject}/ses-01/anat/{subject}_ses-01_FLAIR.nii.gz"
  output:
    segmentations=protected(expand(
      "mri_processed_data/freesurfer/{{subject}}/mri/{seg}.mgz",
      seg=["aparc+aseg", "aseg", "wmparc"]
    )),
    surfs=protected(expand(
      "mri_processed_data/freesurfer/{{subject}}/surf/{surf}",
      surf=["lh.pial", "rh.pial", "lh.white", "rh.white"]
    ))
  params:
    subject_dir = lambda wc: f"mri_processed_data/freesurfer/{wc.subject}",
    license = "docker/license.txt"
  resources:
    time="48:00:00",
  threads: 12
  container: None
  shell:
    "python scripts/freesurfer.py"
    " -t1 {input.t1} "
    " -o {params.subject_dir}"
    " -l {params.license}"
    ' --flair {input.flair}'
    " --threads {threads}"
