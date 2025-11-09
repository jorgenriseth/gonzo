FROM ghcr.io/prefix-dev/pixi:jammy

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
    software-properties-common && \ 
    add-apt-repository -y ppa:apptainer/ppa && \
    apt-get update

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y \
  wget \ 
  fuse2fs \
  squashfuse \
  gocryptfs \
  apptainer-suid \
  tzdata

WORKDIR /opt
ENV PATH="/opt/greedy-1.3.0-alpha-Linux-gcc64/bin:$PATH"
RUN wget https://sourceforge.net/projects/greedy-reg/files/Nightly/greedy-nightly-Linux-gcc64.tar.gz/download -O /opt/greedy.tar.gz \
  && tar xvfz greedy.tar.gz \
  && rm greedy.tar.gz

WORKDIR /gonzo

# 2. Copy application dependencies (pixi install runs as root, so files are root-owned)
COPY pyproject.toml pixi.lock ./
RUN pixi install --locked

# 3. Copy application code
COPY Snakefile snakeconfig.yaml ./
COPY scripts/ ./scripts/
COPY snakeprofiles/ ./snakeprofiles/
COPY workflows/ ./workflows/

RUN groupadd -r gonzo_group && useradd -r -g gonzo_group -s /bin/bash gonzo_user
RUN chown -R gonzo_user:gonzo_group /gonzo
USER gonzo_user

# --- Execution ---
ENTRYPOINT [ "pixi", "run" ]

#
# ###
# COPY pixi.lock pyproject.toml Snakefile snakeconfig.yaml scripts snakeprofiles workflows Snakefile /gonzo/
#
# RUN pixi pixi install --locked -e default
# RUN pixi update && pixi install --locked -e default
# # RUN pixi shell-hook -s bash > /shell-hook
# # RUN echo "#!/bin/bash" > /gonzo/entrypoint.sh
# # RUN cat /shell-hook >> /gonzo/entrypoint.sh
# # RUN echo 'exec "$@"' >> /gonzo/entrypoint.sh
#
# CMD [ "pixi", "run" ]
