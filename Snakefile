import os
import numpy as np
from pathlib import Path
shell.executable("bash")

configfile: "snakeconfig.yaml"
container: "docker://jorgenriseth/gonzo:v0.1.0"

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
