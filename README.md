# Gonzo: Human brain MRI data of CSF-tracer evolution over 72h for data-integrated simulations
This repository documents the processing pipeline for the Gonzo dataset containing dynamic contrast-enhanced MRI-images following intrathecal injection of gadobutrol in a healthy human being. 
The data record is available at (Zenodo-link). 

This document describes how to setup and run each step of the processing pipeline. If you are only interested in downloading the data, you can skip ahead to [download the data](#download-the-data).
## Setup
### Dependencies
- `FreeSurfer`
- `FSL`
- `snakemake`
- `conda`/`mamba`
- `greedy` (https://github.com/pyushkevich/greedy)
- `gmri2fem`: (https://github.com/jorgenriseth/gMRI2FEM)

Either consult their web-pages or see the `%post`-section in `singularity/fs-greedy.def` for instructions on how to install FreeSurfer, greedy and conda.

## Setup
``` bash
conda env create -n gmri2fem -f environment.yml
conda activate gmri2fem
```

### Python-environment:
Assuming `conda` is installed, create and activate the environment by running
```bash
conda env create -n gmri2fem -f environment.yml
conda activate gmri2fem
```

### Download the data
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

### `snakeconfig`
By default the pipeline only generates the mesh for a single resolution, defined by the `SVMTK` resolution argument. If you want higher or lower resolutions, these can be specified in the `snakeconfig.yaml`-file in the root folder.
```bash
resolution: [32,]  # list of desired SVMTK-resolutions to generate the meshes for.
```

### Source
- `Snakefile`: Top-level snakefile defining each step of the processing pipeline. 
- `workflows/`: Contains files to be imported into the top-level `Snakefile` and specifies workflows in a modular way.

### Data
The dataset is split into two main directories,
- #### `mri_dataset`
    The `mri_dataset` follows a BIDS-like structure and should contain the following directories
    - `sub-01`: MRI-data converted from DICOM-format to Nifti. For further details on the conversion see `notebooks/Gonzo-DICOM-extraction.ipynb`.
        - Organized according to: 
            `sub-01/ses-[XX]/[anat|dti|mixed]/sub-01_ses-[XX]_ADDITIONALINFO.nii.gz`.
        - All MRI-images comes with a "sidecar"-file in `json`-format providing additional information in the same directory as the image.
    - `derivatives/sub-01`: Contains MRI-data directly derived from the Niftii-files in the subject folders, such as T1-maps derived from LookLocker using NordicICE, or from Mixed-sequences using the provided code. Also contains a table with sequence acquisition times in seconds, relative to injection_time.

- ### `mri_processed_data`
    The `mri_processed_data`-folder contains information and data which are not organized according to the `BIDS`-format, either due to incompatibility of software, or if another organization greatly simplifies processing.
    It will typically contain the following directories:
    - `freesurfer/sub-01`: Output of Freesurfer's `recon-all` for given subject.
    - `sub-01`: Folder for processed data for the given subject, such as registered images, concentration-estimates meshes and statistics.


Note that the `snakemake`-files in `workflows_additional` specifies workflows by desired outputs, necessary inputs, and shell command to be executed in a relatively easy to read format. Consulting these files might answer several questions regarding the expected structure.


