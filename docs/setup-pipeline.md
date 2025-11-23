# Setup & Running the Pipeline

This guide shows how to install the necessary dependencies and execute parts of,
or the full, data processing pipeline for the data included in the data record
The pipeline was built and tested on a Linux x86-64 platform. Although there
might be workarounds for MacOS and Windows with virtualization, containers or
other compatibility layers such as Rosetta, the instructions assumes you are on
a Debian Linux x86-64 computer.

We rely on the [Pixi package manager by prefix.dev](https://pixi.sh/latest/),
and [Apptainer](https://apptainer.org/), to create a reproducible setup which
may be ported to HPC clusters for executing the pipeline. If this does not work
for you, for some reason, guidelines for installing the necessary dependencies
are provided below.

## Setup

Install Apptainer with necessary dependencies for setting up user namespaces.

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

**Note**: If you want to run this on an HPC-cluster, you will typically not have
admin rights, but Apptainer (or Singularity) will typically already be installed
on HPC-clusters. Consult with your system documentation or you local admin for
instructions on using it.

To manage python dependencies, we recommend using the `pixi` package manager,
which plays well with both `conda` and `PyPI`-packages. To download the pixi
package manager:

```bash
curl -fsSL https://pixi.sh/install.sh | sh
```

Activate the pixi environment (if you have any issues, try to deactivate your
conda environment), and activate post-link-scripts needed by fsl.

```bash
pixi shell --run-post-link-scripts
```

Download the source-data, and unpack into `mri_dataset`

```bash
python scripts/zenodo_download.py --filename mri-dataset.zip --output /tmp
unzip -o /tmp/mri-dataset.zip -d .
```

Download the `jorgenriseth/gonzo:latest` container for use with apptainer

```bash
apptainer build gonzo-pixi.sif docker://jorgenriseth/gonzo:latest
```

Acquire a FreeSurfer license from
(<https://surfer.nmr.mgh.harvard.edu/fswiki/License>), and move the license-file
into `./docker/license.txt` if you're using singularity (yeah, I know the
directory naming is suboptimal).

## Executing the pipeline

The processing pipeline is set up to be run using
[Snakemake](https://snakemake.github.io/). Snakemake allows you to specify a
file to be built, and it will find necessary input files, and determines which
workflows needs to be executed to produce the given output. The command

```bash
snakemake mri_processed_data/sub-01/concentrations/sub-01_ses-02_concentration.nii.gz --dry-run -p
```

will give a summary of all workflows required to produce the first post-contrast
concentration map, and print the command which would be run. To execute, remove
the `--dry-run`-flag.

Assuming that dependencies are installed, the pixi environment is activated, and
the raw data is downloaded, the entire pipeline may be run by executing the
following command from the root directory:

```bash
snakemake --profile snakeprofiles/local-singularity --cores all -p
```

**NB1**: Running the pipeline in its entirety will typically take 24-48h on a
medium level laptop. Using a cluster allows for greater parallellization and
will typically allow the pipeline to finish within the day.

**NB2**: Some of the software in the pipeline can be somewhat fickle, and may
crash if the total memory load gets too large. As Snakemake attempts to run
independent rules in parallell, this can happen often. The easy fix is to retry
the runs with a lower thread/core count, as specified by the `--cores` option.
The better solution, is to use a cluster. See the Snakemake documentation for
details on
[cluster execution](https://snakemake.github.io/snakemake-plugin-catalog/plugins/executor/cluster-generic.html)
or configuring
[profiles](https://snakemake.readthedocs.io/en/stable/executing/cli.html#profiles).

## Troubleshooting

### Apptainer Namespace Errors

**NB:** If you get an error saying:

```
ERROR  : Could not write info to setgroups: Permission denied
ERROR  : Error while waiting event for user namespace mappings: no event received
```

it is probably because Ubuntu 23.10 and later versions does not allow creation
of unprivileged user namespaces by default. To fix it, follow these instructions
found in apptainers INSTALL.md,
(<https://github.com/apptainer/apptainer/blob/release-1.3/INSTALL.md#apparmor-profile-ubuntu-2310>)

## Alternative Setup

### Conda

If you for some reason prefer to use Conda over Pixi, a conda environment may be
installed by

```bash
conda env create -f envs/gonzo.yml
```

### Local install

If you hare having trouble executing the pipeline with the pixi and Apptainer
setup, you could try to run it locally on you computer instead. In addition to
all packages specified in the pixi/conda environment, the pipeline relies on

- _[FreeSurfer](https://surfer.nmr.mgh.harvard.edu/) (v.7.4.1 used for the data
  record)_: Requires Unix system (e.g. Linux or MacOS). May optionally be
  replaced by FastSurfer. Note that FreeSurfer require a free license to run,
  which may be acquired on their web page.

- _[FastSurfer](https://deep-mi.org/research/fastsurfer/)_: Drop-in replacement
  for FreeSurfer, using deep-learning for image segmentation, and a different
  surface reconstruction algorithm. Note that the surface reconstruction still
  relies partially on FreeSurfer, and a FreeSurfer license is still required.
  requires a free license to run, which may be acquired on their web page

- _[Greedy](https://greedy.readthedocs.io/en/latest/): Fast Deformable
  Registration for 2D and 3D Medical Images_: Comes bundles with ITK-snap, or
  can be installed separately from souce or by downloading binaries for windows
  or Linux. Note that `greedy` is somewhat memory-intensive and might require
  20-32GB RAM to work properly. Also available as docker image
  (<https://hub.docker.com/r/jorgenriseth/greedy/tags>
