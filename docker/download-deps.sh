#!/bin/bash
mkdir -p deps
wget https://fsl.fmrib.ox.ac.uk/fsldownloads/fslconda/releases/fslinstaller.py -O deps/fslinstaller.py
wget https://surfer.nmr.mgh.harvard.edu/pub/dist/freesurfer/7.4.1/freesurfer_ubuntu22-7.4.1_amd64.deb -O deps/freesurfer_ubuntu22-7.4.1_amd64.deb
wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh -O deps/Miniforge3-Linux-x86_64.sh
wget https://sourceforge.net/projects/greedy-reg/files/Nightly/greedy-nightly-Linux-gcc64.tar.gz/download -O deps/greedy.tar.gz
git clone --branch stable https://github.com/Deep-MI/FastSurfer.git deps/FastSurfer
