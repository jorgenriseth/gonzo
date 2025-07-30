FROM ghcr.io/prefix-dev/pixi:latest

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
    wget

WORKDIR /opt
ENV PATH="/opt/greedy-1.3.0-alpha-Linux-gcc64/bin:$PATH"
RUN  wget https://sourceforge.net/projects/greedy-reg/files/Nightly/greedy-nightly-Linux-gcc64.tar.gz/download -O /opt/greedy.tar.gz \ 
  && tar xvfz greedy.tar.gz \
  && rm greedy.tar.gz


# WORKDIR /
# COPY gmri2fem /gmri2fem

# NOTE: This command assumes your local pixi.lock is up-to-date.
# Before building, run `pixi install` locally to sync your lock file.
WORKDIR /gonzo
COPY pyproject.toml pixi.lock ./
RUN pixi install --locked

# --- Application Code Layer ---
# Now, copy the rest of your application source code.
# Changes to your code from this point on will not require re-installing all the dependencies,
# making subsequent builds much faster.
# Note: I've cleaned up the COPY command to be more explicit and removed the duplicate Snakefile.
COPY Snakefile snakeconfig.yaml ./
COPY scripts/ ./scripts/
COPY snakeprofiles/ ./snakeprofiles/
COPY workflows/ ./workflows/

# --- Execution ---
# Use ENTRYPOINT to make your container act like an executable.
# This will execute the default task defined in your pyproject.toml.
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
