import os
import numpy as np
from pathlib import Path


configfile: "snakeconfig.yaml"
wildcard_constraints:
  session = "ses-\d{2}"

if "subjects" in config:
	SUBJECTS=config["subjects"]
else:
  SUBJECTS = [p.stem for p in Path("data/mri_dataset/sourcedata").glob("sub-*")]
  config["subjects"] = SUBJECTS

SESSIONS = {
  subject: sorted([p.stem for p in Path(f"data/mri_dataset/sourcedata/{subject}").glob("ses-*")])
  for subject in SUBJECTS
}
config["sessions"] = SESSIONS

include: "workflows/T1maps"
include: "workflows/register"
include: "workflows/concentration-estimate"
include: "workflows/dti"
include: "workflows/mesh-generation"
include: "workflows/mri2fem"
# include: "workflows/recon-all"
# include: "workflows/T1maps"
# include: "workflows/T1w_signal_intensities"
# include: "workflows/statistics"

