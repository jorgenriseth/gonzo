import os
import numpy as np
from pathlib import Path

configfile: "snakeconfig.yaml"

wildcard_constraints:
  session = r"ses-\d{2}",
  resolution = r"\d+"

if "subjects" in config:
	SUBJECTS=config["subjects"]
else:
  SUBJECTS = [p.stem for p in Path("mri_dataset/sourcedata").glob("sub-*")]
  config["subjects"] = SUBJECTS

if "ignore_subjects" in config:
  for subject in config["ignore_subjects"]:
    SUBJECTS.remove(subject)
  config["subjects"] = SUBJECTS

SESSIONS = {
  subject: sorted([p.stem for p in Path(f"mri_dataset/sourcedata/{subject}").glob("ses-*")])
  for subject in SUBJECTS
}
config["sessions"] = SESSIONS
config["FS_DIR"] = "mri_processed_data/freesurfer/{subject}"

include: "workflows/T1maps"
include: "workflows/T1w"
include: "workflows/register"
include: "workflows/segment"
include: "workflows/concentration-estimate"
include: "workflows/statistics"
include: "workflows/dti"
include: "workflows/mesh-generation"
include: "workflows/mri2fem"
include: "workflows/recon-all"
