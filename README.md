# Gonzo: Human brain MRI data of CSF-tracer evolution over 72h for data-integrated simulations

This repository documents the processing pipeline for the Gonzo dataset
containing dynamic contrast-enhanced MRI-images following intrathecal injection
of gadobutrol in a healthy human being. The data record is available at
<https://doi.org/10.1101/2025.07.23.25331971> ,and is accompanied by a data
descriptor available at <https://doi.org/10.5281/zenodo.14266867>

This document describes how to setup and run each step of the processing
pipeline. If you are only interested in downloading the data, you can skip ahead
to [download the data](#download-the-data).

## Install dependencies

```bash
sudo apt-get update
sudo apt-get install -y software-properties-common \
add-apt-repository -y ppa:apptainer/ppa
sudo apt-get update # Rerun after added repository
sudo apt-get install -y \
  wget \
  fuse2fs \
  squashfuse \
  gocryptfs \
  apptainer-suid \
```

The pipeline relies heavily on both python and non-python dependencies. The main
components are

- `FreeSurfer` and/or `FastSurfer`: The current pipeline runs scripts which
  leverages the official docker containers, but the surface reconstruction and
  MRI segmentation may alternatively be run with a local installation of
  FreeSurfer/FastSurfer. See their official web pages for installation
  instructions, and confer with `scripts/freesurfer.py` or
  `scripts/fastsurfer.py` for details on how to run them in current pipeline.
- `FSL` - Only a subset of the commands are necessary. These are available
  through conda by adding the FSL conda channel (see pyproject.toml for link.)
- `greedy` (<https://github.com/pyushkevich/greedy>) - Image registration.
  `greedy` may be memory hungry, so for computers with limited resources, you
  might have to look into alternatives like
- `gmri2fem`: (<https://github.com/jorgenriseth/gMRI2FEM>)
- `fuse2fs`: `sudo apt-get install fuse2fs`
  > > > > > > > 6290920 (updated dependency description in README)

```bash
sudo apt-get update
sudo apt-get install -y software-properties-common
sudo add-apt-repository -y ppa:apptainer/ppa
sudo apt-get update # Rerun after added repository
sudo apt-get install -y \
  wget \
  fuse2fs \
  squashfuse \
  gocryptfs \
  apptainer-suid
```

The pipeline may be run by relying on the `pixi` package manager and singularity
using the instructions below.

- Download the pixi package manager:

  ```bash
  curl -fsSL https://pixi.sh/install.sh | sh
  ```

- Activate the pixi environment (if you have any issues, try to deactivate your
  conda environment), and activate post-link-scripts needed by fsl.

  ```bash
  pixi shell --run-post-link-scripts
  ```

- Download the source-data, and unpack into `mri_dataset`

  ```bash
  python scripts/zenodo_download.py --filename mri-dataset.zip --output /tmp &&
  unzip -o /tmp/mri-dataset.zip -d .
  ```

- Download the jorgenriseth/gonzo:latest container for use with singularity

  ```bash
  apptainer build gonzo-pixi.sif docker://jorgenriseth/gonzo:latest
  ```

- Acquire a FreeSurfer license from
  (<https://surfer.nmr.mgh.harvard.edu/fswiki/License>), and move the
  license-file into `./docker/license.txt` if you're using singularity (yeah, I
  know the location might be confusing).

- Execute the pipeline

  ```bash
  snakemake --profile snakeprofiles/local-singularity --cores all -p
  ```

### Troubleshooting

**NB:** If you get an error saying:

```
ERROR  : Could not write info to setgroups: Permission denied
ERROR  : Error while waiting event for user namespace mappings: no event received
```

it is probably because Ubuntu 23.10 and later versions does not allow creation
of unprivileged user namespaces by default. To fix it, follow these instructions
found in apptainers INSTALL.md,
(<https://github.com/apptainer/apptainer/blob/release-1.3/INSTALL.md#apparmor-profile-ubuntu-2310>)

### Figure creation

#### MRI-visualisations and validation

See the jupyter notebooks in `docs/` for how the images in the article are
created.

#### Monte-carlo noise estimation

Several scripts for investigating the effect of noise on $T_1$-estimates for
both the Look-Locker and the mixed IR/SE sequence are available in
`scripts/mri_noise_analysis`. Change to that directory and run the scripts from
command line. To see possible command line arguments, run e.g.

```bash
python plot_noise_combined.py --help
```

The image included in the article was created by using the default arguments.

### Install conda environment

If you prefer to work with `conda`, the pixi environment have been exported to a
conda environment file in `envs`, and may be installed by

```bash
conda env create -n gonzo -f envs/gonzo.yml
```

### Download the data

Information regarding the organization of the data may be found together with
the data record at: <https://zenodo.org/uploads/14266867>. The script
`scripts/zenodo_download.py` uses the Zenodo REST API to list and/or download
all or specific files.

```bash
ACCESS_TOKEN=[Your Zenodo API Token]
API_URL="https://zenodo.org/api/deposit/depositions/14266867"
```

Note that the Zenodo API token will not be needed once the record is made
public, and can be left empty. Once the `.env`-file have been created, you can
list or download the data files by:

```bash
export ZENODO_ACCESS_TOKEN=[Your Zenodo API Token]

# List all available files in the repo
python scripts/zenodo_download.py --list

# Download  all files into the directory 'outputdir'
python scripts/zenodo_download.py --all  --output outputdir

# Download only the file "README.md" into the current directory
python scripts/zenodo_download.py --filename README.md --output .
```
