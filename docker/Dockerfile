FROM ghcr.io/prefix-dev/pixi:0.83.0-jammy

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
      software-properties-common ca-certificates wget && \
    add-apt-repository -y ppa:apptainer/ppa && \
    apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
      fuse2fs squashfuse gocryptfs apptainer-suid tzdata && \
    apt-get clean

WORKDIR /opt
ENV PATH="/opt/greedy-1.3.0-alpha-Linux-gcc64/bin:$PATH"
RUN wget https://sourceforge.net/projects/greedy-reg/files/Nightly/greedy-nightly-Linux-gcc64.tar.gz/download -O /opt/greedy.tar.gz \
  && tar xvfz greedy.tar.gz \
  && rm greedy.tar.gz

WORKDIR /gonzo
# This environment is generated and validated before image promotion.
COPY envs/release/pixi.toml envs/release/pixi.lock ./
RUN pixi install --locked --run-post-link-scripts

COPY Snakefile snakeconfig.yaml ./
COPY build-record/pipeline-leaf-files.txt ./build-record/pipeline-leaf-files.txt
COPY scripts/ ./scripts/
COPY snakeprofiles/ ./snakeprofiles/
COPY workflows/ ./workflows/

RUN groupadd -r gonzo_group && useradd -r -g gonzo_group -s /bin/bash gonzo_user && \
    chown -R gonzo_user:gonzo_group /gonzo
USER gonzo_user
RUN pixi run --locked python scripts/validate_environment.py
ENTRYPOINT ["pixi", "run", "--locked"]
