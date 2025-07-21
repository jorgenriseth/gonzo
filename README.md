# Gonzo: Human brain MRI data of CSF-tracer evolution over 72h for data-integrated simulations

This repository documents the processing pipeline for the Gonzo dataset
containing dynamic contrast-enhanced MRI-images following intrathecal injection
of gadobutrol in a healthy human being. The data record is available at
(Zenodo-link).

This document describes how to setup and run each step of the processing
pipeline. If you are only interested in downloading the data, you can skip
ahead to [download the data](#download-the-data).

## Setup

### Dependencies

- `FreeSurfer` and/or `FastSurfer`
- `FSL`
- `conda/mamba`
- `greedy` (<https://github.com/pyushkevich/greedy>)
- `gmri2fem`: (<https://github.com/jorgenriseth/gMRI2FEM>)

Either consult their web-pages or see the `%post`-section in
`singularity/gonzo.def` for instructions on how to install FreeSurfer, greedy
and conda.

### Install conda environment

```bash
conda env create -n gonzo -f envs/gonzo.yml
```

### Download the data

Information regarding the organization of the data may be found together with the data record at: <https://zenodo.org/uploads/14266867>.
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

# Download only the file "README.md" into the current directory
python scripts/zenodo_download.py --filename README.md --output .
```

### Run pipeline

The recommended way to run the pipeline is using singularity:. Necessary preparation:

- Download the sourcedata, and unpack into the expected location in `mri_dataset`:

  ```bash
  python scripts/zenodo_download.py --filename mri-dataset.zip --output /tmp &&
  unzip -o /tmp/mri-dataset.zip -d .
  ```

- Acquire a FreeSurfer license from (<https://surfer.nmr.mgh.harvard.edu/fswiki/License>), and move the license-file into `$FREESURFER_HOME/license.txt`, (or into `./docker/license.txt if you're using singularity.).

Assuming that the sourcedata from `mri_dataset.zip` has been downloaded and unopacked, the following command will run the entire pipeline, in a singularity container, using conda

```bash
snakemake --cores 'all' --profile snakeprofiles/local
```

If you rather want to install all dependencies locally, and run the pipeline without using singularity,

```bash
snakemake --cores 'all' --use-conda
```

### Noise-estimation

Several scripts for investigating the effect of noise on $T_1$-estimates for both the Look-Locker and the mixed IR/SE sequence are available in `scripts/mri_noise_analysis`. Change to that directory and run the scripts from command line. To see possible command line arguments, run e.g.

```bash
python plot_noise_combined.py --help
```

The image included in the article was created by using the default arguments.

## Archive below

---

#### FastSurfer

```bash
FASTSURFER_HOME=[path to your fastsurfer installation]
echo "export PYTHONPATH=\"\${PYTHONPATH}:$FASTUSRFER_HOME" > $CONDA_PREFIX/etc/conda/activate.d/activate-fastsurfer.sh
echo "export PATH=\"$FASTSURFER_HOME:\$PATH\"" >> $CONDA_PREFIX/etc/conda/activate.d/activate-fastsurfer.sh
```

### Clone the necessary repositories

```bash
git clone https://github.com/jorgenriseth/gonzo
cd gonzo
```

### Python-environment

Assuming `conda` is installed, create and activate the environment by running

```bash
source $FREESURFER_HOME/SetUpFreeSurfer.sh
conda env create -n gonzo -f environment.yml
conda activate gonzo
echo "export PYTHONPATH=\"\${PYTHONPATH}:$PWD\"" > $CONDA_PREFIX/etc/conda/activate.d/activate-fastsurfer.sh
echo "export PATH=\"$PWD:\$PATH\"" >> $CONDA_PREFIX/etc/conda/activate.d/activate-fastsurfer.sh
conda activate gonzo
```

**NB:** Make sure you source `SetupFreeSurfer.sh` before activating the `conda` environment. `SetupFreeSurfer` does it's own activation of a python-environment, which would overwrite e.g. the python-path set by your environment.

### Docker

We also provide a docker image with necessary dependencies to run the pipeline. The image can be pulled from Docker hub

```bash
docker pull jorgenriseth/gonzo:latest
```

or it can be built from the local Dockerfile by

```bash
bash docker/download-deps.sh;
docker build -t jorgenriseth/gonzo -f docker/Dockerfile .
```

Note that if you want to run the FreeSurfer/FastSurfer commands, you need to download a (free) license file from FreeSurfer web page.
This needs to be mounted into the root-directory of the container,

```bash
docker run --rm -it -v [path/to/license.txt]:/license.txt -v $PWD:/gonzo/gonzo jorgenriseth/gonzo bash
```

and from within the container, run

```bash
snakemake --use-conda -p
```

### Singularity

If desired, the pipeline can be run in a singularity-container. Note that
a personal license-file is needed for all FreeSurfer-dependencies (also the
surface reconstruction pipeline in FastSurfer), which you may get for free
on the FreeSurfer web page. Once acquired, the license should be moved to
`singularity/license.txt`.

To build the container, run from the `gonzo` root directory:

```bash
singularity build singularity/gonzo-conda.sif singularity/gonzo-conda.def;
singularity build singularity/gonzo.sif singularity/gonzo.def
```

Once built, the `snakemake` pipeline may be run by container can be run using

# TODO: Check that this is still best way to do it

```bash
pixi run snakemake {file-to-process} --use-singularity
```

### Download the data

Information regarding the organization of the data may be found together with the data record at: <https://zenodo.org/uploads/14266867>.
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

To download only and unpack only the data, such that you may run the entire pipeline,

```bash
python scripts/zenodo_download.py --filename mri-dataset.zip --output /tmp &&
unzip -o /tmp/mri-dataset.zip -d .
```

### Run `snakemake`

```bash
pixi run snakemake data.vtk [--dry-run]  # Recommend dry-run first to see the list of jobs needed to generate the files. The remove them to run the jobs.
```

NB: If you have already activated the environment using `pixi shell`, you can drop `pixi run` from this command.

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
    Note that the `snakemake`-files in `workflows` specifies workflows by desired outputs, necessary inputs, and shell command to be executed in a relatively easy to read format. Consulting these files might answer several questions regarding the expected structure.
