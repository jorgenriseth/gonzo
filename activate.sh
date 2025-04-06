#!/bin/bash
source /gonzo/conda/etc/profile.d/conda.sh
if [[ -n "$CONDA_DEFAULT_ENV" ]]; then
  CURRENT_ENV=$CONDA_DEFAULT_ENV
  conda deactivate
  source $FREESURFER_HOME/SetUpFreeSurfer.sh
else
  CURRENT_ENV=gonzo
  source ${FREESURFER_HOME}/SetUpFreeSurfer.sh
fi
conda activate $CURRENT_ENV
export PATH="$CURRENT_ENV/bin:$PATH"
