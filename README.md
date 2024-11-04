## Gonzo - MRI Dataset

This repository contains code for processing glymphatic MRI-images, i.e. contrast-enhanced brain images, with special focus on concentration-estimation and conversion into dolfin for mathematical modelling of brain tracer transport using the finite element method. 

While this repository may be installed as a python-package and used freely as such, it also contains a `snakemake` processing pipeline built around estimating concentrations from T1-weighted images or T1-maps, and mapping them to `dolfin`-functions. This, of course, relies on having the available data and organizing it according to the data section below.

## Setup
### Python-environment:
Assuming `conda`/`mamba` is installed, create an environment by running
```bash
conda env create -n gmri2fem -f environment.yml
conda activate gmri2fem
```
and install the current repository as a package (optional `-e` for editable) using 
```bash
pip install [-e] .
```

### General dependencies
The repository relies on the following software:
- `FreeSurfer`
- `greedy`
- `dcm2niix`
- `conda`/`mamba`

Either consult their web-pages or see the `%post`-section in `singularity/fs-greedy.def` for instructions on how to install these dependencies (or build and use the singularity-container `singularity/gmri2fem.def` to install dependencies and python-environment).

### `snakeconfig`
Several parts of the pipeline can be configured to run for only for specific subjects or with specific settings. These values can be set in  the `snakeconfig.yaml` in the root folder.
- TODO: remove resource-specifications such as num-threads to `snakeprofiles`
- TODO: add a default for num-sessions which allows for subject-specific number of sessions
```bash
subjects: [] # list of subject-names to include when running general workflows
resolution: [32]  # list of desired SVMTK-resolutions to generate meshes and run simulations for
sim_threads: 8  # Number of cores to use for simulatiohns
recon_threads: 1  # number of cores to use for regon-all
num_sessions: 5   # Expected number of sessions
```

### Data
The `snakemake`-pipeline requires a dataset-structure loosely based on the BIDS-data structure in a directory called `data` (could also be a symlink to an already existing dataset, although this requires some care if running with `singularity`-containers). The dataset is split into two main directories:
- `mri_dataset`
- `mri_processed_data`

### `data/mri_dataset`
The `mri_dataset`-folder should contain the following:
- `sub-[subjectid]`: MRI-data converted from DICOM-format to Niftii, using either `dcm2niix` or the script `code/extract_mixed_sequence.py`.  Organized according to `sub-[subjectid]/ses-[XX]/[anat|dti]/sub-[subjectid]_ses-[XX]_ADDITIONALINFO.nii.gz`. All MRI-images comes with a "sidecar"-file in `json`-format providing additional information.
- `derivatives/sub-[subjectid]`: Contains MRI-data directly derived from the Niftii-files in the subject folders, such as T1-maps derived from LookLocker using NordicICE, or from Mixed-sequences using the provided code. Also contains a table with sequence acquisition times in seconds, relative to injection_time.
- `code`: Contains scripts and code that were used to extract images or information from the DICOM sourcedata. We strive to keep any code interacting with DICOM-files in this directory, rather than in the python-package, since the source-data is often organized without following any specific convention.
- `Snakefile`: Snakefile describing workflows with scripts and code in the `code`-folder
- (Optional) `sourcedata`: DICOM-files. Organized by session according to `sourcedata/sub-[subjectid]/[raw_datelabel]/[raw_sessionlabel]/`. Will potentially be excluded from public dataset.


### `data/mri_processed_data`
The `mri_processed_data`-folder contains information and data which are not organized according to the `BIDS`-format, either due to incompatibility of software, or if another organization greatly simplifies processing.
It will typically contain the following directories:
- `freesurfer/sub-[subjectid]`: Output of Freesurfer's `recon-all` for given subject.
- `sub-[subjectid]`: Folder for processed data for the given subject, such as registered images, concentration-estimates meshes and statistics.


Note that the `snakemake`-files in `workflows_additional` specifies workflows by desired outputs, necessary inputs, and shell command to be executed in a relatively easy to read format. Consulting these files might answer several questions regarding the expected structure.


