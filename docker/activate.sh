#!/bin/bash
. /gonzo/conda/etc/profile.d/conda.sh
if [[ -n "$CONDA_DEFAULT_ENV" ]]; then
  echo $CONDA_DEFAULT_ENV
  CURRENT_ENV=$CONDA_DEFAULT_ENV
  conda deactivate
else
  CURRENT_ENV=gonzo
fi
export FASTSURFER_HOME=/gonzo/FastSurfer
source $FREESURFER_HOME/SetUpFreeSurfer.sh
conda activate $CURRENT_ENV
export PATH="$CURRENT_ENV/bin:$PATH"
export PYTHONPATH="$PYTHONPATH:/gonzo/FastSurfer"
export DIJITSO_CACHE_DIR="$PWD/.dijitso_cache"
