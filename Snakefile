import os
import numpy as np
from pathlib import Path
shell.executable("bash")

configfile: "snakeconfig.yaml"
container: "singularity/pixi.sif"

if DeploymentMethod.APPTAINER in workflow.deployment_settings.deployment_method:
  shell.prefix(
    "set -eo pipefail; "
    "pixi run "
    # + "source /opt/conda/etc/profile.d/conda.sh && "
    # + "conda activate $CONDA_ENV_NAME && "
    #    + "ls -l && "
  )

wildcard_constraints:
  session = r"ses-\d{2}",
  resolution = r"\d+"

if "subjects" in config:
	SUBJECTS=config["subjects"]
else:
  SUBJECTS = [p.stem for p in Path("mri_dataset/").glob("sub-*")]
  config["subjects"] = SUBJECTS

if "ignore_subjects" in config:
  for subject in config["ignore_subjects"]:
    SUBJECTS.remove(subject)
  config["subjects"] = SUBJECTS

SESSIONS = {
  subject: sorted([p.stem for p in Path(f"mri_dataset/{subject}").glob("ses-*")])
  for subject in SUBJECTS
}
config["sessions"] = SESSIONS
config["FS_DIR"] = "mri_processed_data/freesurfer/{subject}"


include: "workflows/T1maps.smk"
include: "workflows/T1w.smk"
include: "workflows/register.smk"
include: "workflows/segment.smk"
include: "workflows/concentration-estimate.smk"
include: "workflows/dti.smk"
include: "workflows/statistics.smk"
include: "workflows/mesh-generation.smk"
include: "workflows/mri2fem.smk"
#include: "workflows/recon-all.smk"
