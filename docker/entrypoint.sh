#!/bin/bash --login
source $FREESURFER_HOME/SetUpFreeSurfer.sh
. /gonzo/conda/etc/profile.d/conda.sh
conda activate gonzo

exec "$@"
