# Start with the same base image as the Apptainer definition
FROM deepmi/fastsurfer:cpu-v2.3.3
USER root
WORKDIR /

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

# Download and install greedy
WORKDIR /opt
ENV PATH="/opt/greedy-1.3.0-alpha-Linux-gcc64/bin:$PATH"
RUN wget --no-verbose --show-progress --progress=bar:force:noscroll \
  https://sourceforge.net/projects/greedy-reg/files/Nightly/greedy-nightly-Linux-gcc64.tar.gz/download \
  -O greedy.tar.gz \
  && tar xvfz greedy.tar.gz \
  && rm greedy.tar.gz

# Download and install FSL
WORKDIR /opt
ENV FSLDIR=/opt/fsl
ENV PATH="/opt/fsl/share/fsl/bin:$PATH"
RUN wget https://fsl.fmrib.ox.ac.uk/fsldownloads/fslconda/releases/fslinstaller.py && \
    python fslinstaller.py -d /opt/fsl && \
    rm fslinstaller.py && \
    echo '. ${FSLDIR}/etc/fslconf/fsl.sh' >> /etc/bash.bashrc

# Install Miniforge3 (a conda installer)
ENV PATH="/opt/conda/bin:$PATH"
ENV FS_LICENSE=/license.txt
RUN wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh -O /tmp/Miniforge3.sh && \
    bash /tmp/Miniforge3.sh -b -p /opt/conda && \
    rm /tmp/Miniforge3.sh && \
    /opt/conda/bin/conda update -n base -c conda-forge -y conda


WORKDIR /gonzo
COPY environment.yml environment.yml
RUN /opt/conda/bin/conda env create -n gonzo -f environment.yml && \
    echo '. /opt/conda/etc/profile.d/conda.sh' >> /etc/bash.bashrc && \
    echo 'conda activate gonzo' >> /etc/bash.bashrc

# Create a script that will be used as the entrypoint to ensure conda environment is activated
# Create the nonroot user
RUN useradd -ms /bin/bash nonroot

WORKDIR /
RUN echo '#!/bin/bash --login' > /entrypoint.sh && \
    echo 'source $FREESURFER_HOME/SetUpFreeSurfer.sh' >> /entrypoint.sh && \
    echo '. ${FSLDIR}/etc/fslconf/fsl.sh' >> /entrypoint.sh && \
    echo '. /opt/conda/etc/profile.d/conda.sh' >> /entrypoint.sh && \
    echo "conda activate gonzo" >> /entrypoint.sh && \
    echo 'exec "$@"' >> /entrypoint.sh && \
    chmod +x /entrypoint.sh && \
    chown nonroot:nonroot /entrypoint.sh

USER nonroot

# Set the entrypoint to our script
ENTRYPOINT ["/entrypoint.sh"]
SHELL ["conda", "run", "-n", "gonzo", "/bin/bash", "-c"]
CMD ["conda", "run", "-n", "gonzo", "/bin/bash"]
