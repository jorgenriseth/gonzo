# Start with the same base image as the Apptainer definition
FROM deepmi/fastsurfer:cpu-v2.3.3
USER root

# Create the nonroot user
RUN useradd -ms /bin/bash nonroot
# Install dependencies (equivalent to the %post section)
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
    wget \
    curl \
    bzip2 \
    zip \
    ca-certificates \
    git \
    libncurses-dev

COPY docker/greedy.tar.gz greedy.tar.gz 
COPY docker/freesurfer_ubuntu22-7.4.1_amd64.deb freesurfer_ubuntu22-7.4.1_amd64.deb
COPY docker/fslinstaller.py fslinstaller.py
COPY docker/Miniforge3-Linux-x86_64.sh Miniforge3-Linux-x86_64.sh


# Download and install greedy
#RUN wget --no-verbose --show-progress --progress=bar:force:noscroll \
#  https://sourceforge.net/projects/greedy-reg/files/Nightly/greedy-nightly-Linux-gcc64.tar.gz/download \
#  -O greedy.tar.gz \
RUN tar xvfz greedy.tar.gz \
  && rm greedy.tar.gz

# Download and install freesurfer. Remove installer afterwards to reduce image.
# RUN wget --no-verbose --show-progress --progress=bar:force:noscroll \
#   https://surfer.nmr.mgh.harvard.edu/pub/dist/freesurfer/7.4.1/freesurfer_ubuntu22-7.4.1_amd64.deb \
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y ./freesurfer_ubuntu22-7.4.1_amd64.deb \
  && rm freesurfer_ubuntu22-7.4.1_amd64.deb


# Download and install FSL
RUN wget https://fsl.fmrib.ox.ac.uk/fsldownloads/fslconda/releases/fslinstaller.py && \
    python fslinstaller.py -d /opt/fsl && \
    rm fslinstaller.py

# Install Miniforge3 (a conda installer)
RUN wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh -O /tmp/Miniforge3.sh && \
    bash /tmp/Miniforge3.sh -b -p /opt/conda && \
    rm /tmp/Miniforge3.sh

# Update Conda
RUN /opt/conda/bin/conda update -n base -c conda-forge -y conda

# Set environment variables (equivalent to the %environment section)
ENV FREESURFER_HOME="/usr/local/freesurfer/7.4.1"
ENV FS_LICENSE=/license.txt
ENV FSLDIR=/opt/fsl
ENV PATH=${FSLDIR}/share/fsl/bin:${PATH}
ENV PATH="/usr/local/freesurfer/7.4.1/bin:$PATH"
ENV PATH="/greedy-1.3.0-alpha-Linux-gcc64/bin:$PATH"
ENV DIJITSO_CACHE_DIR="$HOME/.dijitso_cache"
ENV PATH="/opt/conda/bin:$PATH"

# Set up FreeSurfer and FSL when container starts
RUN echo 'source $FREESURFER_HOME/SetUpFreeSurfer.sh' >> /etc/bash.bashrc && \
    echo '. ${FSLDIR}/etc/fslconf/fsl.sh' >> /etc/bash.bashrc && \
    echo '. /opt/conda/etc/profile.d/conda.sh' >> /etc/bash.bashrc


## Set conda environment name (from %arguments in second file)
ENV CONDA_ENV_NAME="gonzo"

# Copy files from the second definition file
# These would typically be in the same directory as your Dockerfile
#RUN mkdir -p /submodules/gmri2fem/src
COPY environment.yml /environment.yml
COPY pyproject.toml /pyproject.toml
#ADD submodules/gmri2fem/pyproject.toml /submodules/gmri2fem/pyproject.toml
#ADD submodules/gmri2fem/src /submodules/gmri2fem/src

# Create conda environment from the copied files (from %post in second file)
RUN /opt/conda/bin/conda env create -n ${CONDA_ENV_NAME} -f /environment.yml

# Activate the conda environment by default
RUN echo 'conda activate ${CONDA_ENV_NAME}' >> /etc/bash.bashrc

# Create a script that will be used as the entrypoint to ensure conda environment is activated
RUN echo '#!/bin/bash' > /entrypoint.sh && \
    echo 'source $FREESURFER_HOME/SetUpFreeSurfer.sh' >> /entrypoint.sh && \
    echo '. ${FSLDIR}/etc/fslconf/fsl.sh' >> /entrypoint.sh && \
    echo '. /opt/conda/etc/profile.d/conda.sh' >> /entrypoint.sh && \
    echo "conda activate ${CONDA_ENV_NAME}" >> /entrypoint.sh && \
    echo 'exec "$@"' >> /entrypoint.sh && \
    chmod +x /entrypoint.sh

USER nonroot

# Set the entrypoint to our script
ENTRYPOINT ["/entrypoint.sh"]

# Default command when container starts
CMD ["/bin/bash"]
