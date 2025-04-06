# Start with the same base image as the Apptainer definition
FROM ubuntu:22.04

# Install dependencies (equivalent to the %post section)
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
    wget \
    curl \
    bzip2 \
    zip \
    ca-certificates \
    git \
    libncurses-dev \
    libgomp1 \
    libxml2 \
    libquadmath0 \
    vim \ 
    python3 \
    tcsh xxd build-essential gfortran \
    libblas-dev liblapack-dev zlib1g-dev \ 
    libxmu-dev libxmu-headers libxi-dev libxt-dev libx11-dev libglu1-mesa-dev
    # && rm -rf /var/lib/apt/lists/*

WORKDIR /gonzo
ENV PATH="/gonzo/greedy-1.3.0-alpha-Linux-gcc64/bin:$PATH"
COPY deps/greedy.tar.gz greedy.tar.gz
# RUN wget --no-verbose --show-progress --progress=bar:force:noscroll \
#   https://sourceforge.net/projects/greedy-reg/files/Nightly/greedy-nightly-Linux-gcc64.tar.gz/download -O greedy.tar.gz \
RUN tar xvfz greedy.tar.gz \
  && rm greedy.tar.gz

ENV PATH="/gonzo/FastSurfer:$PATH"
COPY deps/FastSurfer FastSurfer
#RUN git clone --branch stable https://github.com/Deep-MI/FastSurfer.git

# Download and install FSL
ENV FSLDIR=/gonzo/fsl
COPY deps/fslinstaller.py fslinstaller.py
#RUN wget https://fsl.fmrib.ox.ac.uk/fsldownloads/fslconda/releases/fslinstaller.py && \
RUN python3 fslinstaller.py -d /gonzo/fsl && \
    rm fslinstaller.py

# Download and install freesurfer. Remove installer afterwards to reduce image.
# ENV FREESURFER_HOME="/gonzo/freesurfer"
# RUN wget --no-verbose --show-progress --progress=bar:force:noscroll \
#   https://surfer.nmr.mgh.harvard.edu/pub/dist/freesurfer/7.4.1/freesurfer-linux-ubuntu22_amd64-7.4.1.tar.gz \
#   -O freesurfer.tar.gz \
#   && tar xvfz freesurfer.tar.gz \
#   && rm freesurfer.tar.gz

# Download and install freesurfer. Remove installer afterwards to reduce image.
ENV FREESURFER_HOME="/usr/local/freesurfer/7.4.1"
ENV FS_LICENSE=/license.txt
COPY deps/freesurfer_ubuntu22-7.4.1_amd64.deb freesurfer_ubuntu22-7.4.1_amd64.deb
# RUN wget --no-verbose --show-progress --progress=bar:force:noscroll \
#   https://surfer.nmr.mgh.harvard.edu/pub/dist/freesurfer/7.4.1/freesurfer_ubuntu22-7.4.1_amd64.deb \
RUN DEBIAN_FRONTEND=noninteractive apt install -y ./freesurfer_ubuntu22-7.4.1_amd64.deb \
  && rm freesurfer_ubuntu22-7.4.1_amd64.deb

# Install Miniforge3 (a conda installer)
ENV PATH="/gonzo/conda/bin:$PATH"
ENV FS_LICENSE=/license.txt
COPY deps/Miniforge3-Linux-x86_64.sh Miniforge3.sh
# RUN wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh -O /tmp/Miniforge3.sh && \
RUN bash Miniforge3.sh -b -p /gonzo/conda && \
    rm Miniforge3.sh && \
    /gonzo/conda/bin/conda update -n base -c conda-forge -y conda

# Install the necesary python dependencies
COPY environment.yml environment.yml
RUN /gonzo/conda/bin/conda env create -n gonzo -f environment.yml

# Set the entrypoint to our script
COPY entrypoint.sh /entrypoint.sh
RUN chmod a+x /entrypoint.sh 
ENTRYPOINT ["/entrypoint.sh"]

RUN groupadd -g 1000 nonroot-group && useradd -m -u 1000 -g nonroot-group nonroot \ 
  && mkdir /matlab && chmod a+w /matlab \
  && chmod -R a+w /gonzo/FastSurfer
USER nonroot
