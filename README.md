# Gonzo: Human brain MRI data of CSF-tracer evolution over 72h for data-integrated simulations
This repository documents the processing pipeline for the Gonzo dataset containing dynamic contrast-enhanced MRI-images following intrathecal injection of gadobutrol in a healthy human being. 
The data record is available at (Zenodo-link). 

This document describes how to setup and run each step of the processing pipeline. If you are only interested in downloading the data, you can skip ahead to [download the data](#download-the-data).
## Setup
### Dependencies
- `pixi` Python package manager: https://pixi.sh/latest/. ([Why pixi?](https://ericmjl.github.io/blog/2024/8/16/its-time-to-try-out-pixi/))
- `FreeSurfer`
- `FSL`
- `greedy` (https://github.com/pyushkevich/greedy)
- `gmri2fem`: (https://github.com/jorgenriseth/gMRI2FEM)

Either consult their web-pages or see the `%post`-section in `singularity/fs-greedy.def` for instructions on how to install FreeSurfer, greedy and conda.

## Setup
### Install `pixi`
Install pixi by:
```bash
curl -fsSL https://pixi.sh/install.sh | bash
```
To activate the python environment, run
```bash
pixi shell
```
from the project root. The first time you run this, `pixi` will create the environment and install all necessary packages.

### Download the data
Information regarding the organization of the data may be found together with the data record at: https://zenodo.org/uploads/14266867.
The script `scripts/zenodo_download.py` uses the Zenodo REST API to list and/or download all or specific files.
It requires `pydantic_settings` which is installable through pip. 
To download the data, create an `.env`-file in the root directory of this repository with the following content:
```bash
ACCESS_TOKEN=[Your Zenodo API Token]
API_URL="https://zenodo.org/api/deposit/depositions/14266867"
```
Note that the Zenodo API token wil not be needed once the record is made public, and can be left empty.
Once the `.env`-file have been created, you can list or download the data files by: 
```bash
# List all available files in the repo
python scripts/zenodo_download.py --list 

# Download  all files into the directory 'outputdir'
python scripts/zenodo_download.py --all  --output outputdir

# Download only the file "README.md" into the current directoryp
python scripts/zenodo_download.py --filename README.md --output .
```

### Run `snakemake`
```bash
pixi run snakemake data.vtk [--dry-run]  # Recommend dry-run first to see the list of jobs needed to generate the files. The remove them to run the jobs.
```
NB: If you have already activated the environment using `pixi shell`, you can drop `pixi run` from this command.

### Noise-estimation
Several scripts for investigating the effect of noise on $T_1$-estimates for both the Look-Locker and the mixed IR/SE sequence are available in `scripts/mri_noise_analysis`. Change to that directory and run the scripts from command line. To see possible command line arguments, run e.g.
```bash
python plot_noise_combined.py --help
```

### `snakeconfig`
By default the pipeline only generates the mesh for a single resolution, defined by the `SVMTK` resolution argument. If you want higher or lower resolutions, these can be specified in the `snakeconfig.yaml`-file in the root folder.
```bash
resolution: [32,]  # list of desired SVMTK-resolutions to generate the meshes for.
```

### Source
- `Snakefile`: Top-level snakefile defining each step of the processing pipeline. 
- `workflows/`: Contains files to be imported into the top-level `Snakefile` and specifies workflows in a modular way.

