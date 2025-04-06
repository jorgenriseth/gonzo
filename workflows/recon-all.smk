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
    threads: 0.25 * workflow.cores
    conda: "../envs/fastsurfer.yml"
    shell:
      "run_fastsurfer.sh"
      " --fs_license $(realpath singularity/license.txt)"
      " --t1 $(realpath {input.t1})"
      " --sid {wildcards.subject}"
      " --sd $(realpath -m $(dirname {output[0]})/../..)"
      " --3T"
      " --threads {threads}"
      " --no_hypothal"
      " --viewagg_device 'cpu'"
      " --py 'python'"


rule recon_all_setup:
  input:
    "mri_dataset/{subject}/ses-01/anat/{subject}_ses-01_T1w.nii.gz",
  output:
    "mri_processed_data/freesurfer/{subject}/mri/orig/001.mgz",
  shell:
    "mri_convert {input} {output}"


rule recon_all_setup_FLAIR:
  input:
    "mri_dataset/{subject}/ses-01/anat/{subject}_ses-01_FLAIR.nii.gz",
  output:
    "mri_processed_data/freesurfer/{subject}/mri/orig/FLAIRraw.mgz",
  shell:
    "mri_convert --no_scale 1 {input} {output}"


rule recon_all_setup_T2:
  input:
    "mri_dataset/{subject}/ses-01/anat/{subject}_ses-01_T2w.nii.gz",
  output:
    "mri_processed_data/freesurfer/{subject}/mri/orig/T2raw.mgz",
  shell:
    "mri_convert -c --no_scale 1 {input} {output}"


def recon_input(wildcards):
  t1 = f"mri_processed_data/freesurfer/{wildcards.subject}/mri/orig/001.mgz"
  if "FS-pial-contrast" in config:
    contrast = config["FS-pial-contrast"]
    pial_file = f"mri_processed_data/freesurfer/{wildcards.subject}/mri/orig/{contrast}raw.mgz"
    return [t1, pial_file]
  return [t1]


recon_all_cmd = (
  "recon-all"
  + " -all"
  + " -sd mri_processed_data/freesurfer"
  + " -s {wildcards.subject}"
  + " -parallel"
)
if "FS-pial-contrast" in config:
  contrast = config["FS-pial-contrast"]
  pial_file = f"mri_processed_data/freesurfer/{{wildcards.subject}}/mri/orig/{contrast}raw.mgz"
  recon_all_cmd += f" -{contrast}pial -{contrast} {pial_file}"

rule recon_all:
  input:
    recon_input
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
    f"{recon_all_cmd}"
