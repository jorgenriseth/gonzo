import os
import numpy as np
from pathlib import Path
shell.executable("bash")

configfile: "snakeconfig.yaml"
container: "singularity/gonzo.sif"

if DeploymentMethod.APPTAINER in workflow.deployment_settings.deployment_method:
  shell.prefix(
    "set -eo pipefail; "
    "source /opt/conda/etc/profile.d/conda.sh && "
    "conda activate gonzo && "
)

wildcard_constraints:
  session = r"ses-\d{2}",
  resolution = r"\d+"

SUBJECTS = ["sub-01"]
SESSIONS = {
  subject: sorted([p.stem for p in Path(f"mri_dataset/{subject}").glob("ses-*")])
  for subject in SUBJECTS
}

include: "workflows/T1maps.smk"
include: "workflows/T1w.smk"
include: "workflows/register.smk"
include: "workflows/segment.smk"
include: "workflows/concentration-estimate.smk"
include: "workflows/dti.smk"
include: "workflows/statistics.smk"
include: "workflows/mesh-generation.smk"
include: "workflows/mri2fem.smk"
include: "workflows/recon-all.smk"


def list_leaves():
    with open("build-archive/pipeline-leaf-files.txt") as f:
      return f.read().splitlines()

rule all:
  input: list_leaves()
  output: 
    "build-archive/freesurfer.zip",
    "build-archive/mesh-data.zip",
    "build-archive/mri-dataset.zip",
    "build-archive/mri-dataset-precontrast-only.zip",
    "build-archive/mri-processed.zip",
    "build-archive/surfaces.zip"
  shell:
    "bash ./scripts/archive.sh"


rule download_raw:
  output:
    [
      f"mri_dataset/sub-01/{ses}/anat/sub-01_{ses}_T1w{suffix}"
      for ses in SESSIONS["sub-01"] for suffix in [".nii.gz", ".json"]
    ],
    [
      f"mri_dataset/sub-01/{ses}/anat/sub-01_{ses}_acq-looklocker_IRT1{suffix}"
      for ses in SESSIONS["sub-01"] for suffix in [".nii.gz", ".json", "_trigger_times.txt"]
    ],
    [
      f"mri_dataset/sub-01/{ses}/mixed/sub-01_{ses}_acq-mixed{suffix}" 
      for ses in SESSIONS["sub-01"] 
      for suffix in ["_SE-modulus.nii.gz", "_T1map_scanner.nii.gz", "_IR-corrected-real.nii.gz", ".json", "_meta.json"]
    ],
    [
      f"mri_dataset/sub-01/ses-01/dwi/sub-01_ses-01_acq-multiband_sense_dir-AP_DTI{suffix}"
      for suffix in [".nii.gz", ".bval", ".bvec", ".json", "_ADC.nii.gz"]
    ],
    [
      f"mri_dataset/sub-01/ses-01/dwi/sub-01_ses-01_acq-multiband_sense_dir-PA_b0{suffix}"
      for suffix in [".nii.gz", ".bval", ".bvec", ".json"]
    ],
    [
      f"mri_dataset/sub-01/ses-01/anat/sub-01_ses-01_T2w{suffix}" for suffix in [".nii.gz", ".json"]
    ],
    [
      f"mri_dataset/sub-01/ses-01/anat/sub-01_ses-01_FLAIR{suffix}" for suffix in [".nii.gz", ".json"]
    ],
    "mri_dataset/timetable.tsv"
  shell:
    "python scripts/zenodo_download.py --filename mri-dataset.zip --output /tmp &&" 
    " unzip -o /tmp/mri-dataset.zip -d . "
