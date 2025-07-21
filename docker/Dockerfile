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

WORKDIR /gonzo

# Download and install FSL
ENV FSLDIR=/gonzo/fsl
COPY deps/fslinstaller.py fslinstaller.py
RUN python3 fslinstaller.py -d /gonzo/fsl && \
    rm fslinstaller.py

# Download and install freesurfer. Remove installer afterwards to reduce image.
ENV FREESURFER_HOME="/usr/local/freesurfer/7.4.1"
ENV FS_LICENSE=/license.txt
COPY ./deps/freesurfer_ubuntu22-7.4.1_amd64.deb freesurfer_ubuntu22-7.4.1_amd64.deb
RUN DEBIAN_FRONTEND=noninteractive apt install -y ./freesurfer_ubuntu22-7.4.1_amd64.deb \
  && rm freesurfer_ubuntu22-7.4.1_amd64.deb \
  && rm -rf /var/lib/apt/lists/*


# Install Miniforge3 (a conda installer)
ENV PATH="/gonzo/conda/bin:$PATH"
ENV FS_LICENSE=/license.txt
COPY deps/Miniforge3-Linux-x86_64.sh Miniforge3.sh
RUN bash Miniforge3.sh -b -p /gonzo/conda && \
    rm Miniforge3.sh && \
    /gonzo/conda/bin/conda update -n base -c conda-forge -y conda


ENV PATH="/gonzo/greedy-1.3.0-alpha-Linux-gcc64/bin:$PATH"
COPY deps/greedy.tar.gz greedy.tar.gz
RUN tar xvfz greedy.tar.gz \
  && rm greedy.tar.gz

# Install the necesary python dependencies
COPY envs/gonzo.yml gonzo.yml
COPY envs/fastsurfer.yml fastsurfer.yml
RUN /gonzo/conda/bin/conda env create -n gonzo -f gonzo.yml \
  && /gonzo/conda/bin/conda env create -n fastsurfer -f fastsurfer.yml 

ENV PATH="/gonzo/FastSurfer:$PATH"
ENV PYTHONPATH="$PYTHONPATH:/gonzo/FastSurfer"
RUN git clone --branch stable https://github.com/Deep-MI/FastSurfer.git \
  && chmod -R a+rwx /gonzo/FastSurfer \
  && /gonzo/conda/envs/fastsurfer/bin/python3 /gonzo/FastSurfer/FastSurferCNN/download_checkpoints.py --all


# Set the entrypoint to our script
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod a+x /entrypoint.sh 
ENTRYPOINT ["/entrypoint.sh"]

RUN groupadd -g 1000 nonroot-group && useradd -m -u 1000 -g nonroot-group nonroot \ 
  && mkdir /matlab && chmod a+w /matlab

USER nonroot
