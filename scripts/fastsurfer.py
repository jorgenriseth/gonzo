import shlex
import subprocess
from pathlib import Path
from typing import Optional, Required

import click


@click.command()
@click.option("-t1", type=Path, required=True)
@click.option("-o", "output", type=Path, required=True)
@click.option("-l", "license", type=Path, required=True)
@click.option("--threads", type=int, default=1)
@click.option("--tag", type=str, default="cpu-v2.4.2", help="FastSurfer docker tag")
def run_fastsurfer(
    t1: Path,
    output: Path,
    license: Path,
    tag: str = "cpu-v2.4.2",
    threads: int = 1,
):
    t1_dir, t1_name = t1.parent, t1.name
    fs_dir, subject = output.parent, output.name
    use_cpu = "cpu" in tag
    cmd = f"""
        singularity exec --no-mount home,cwd -e 
        {"-nv" * (not use_cpu)}
        -B "{t1_dir.resolve()}:/data" 
        -B "{fs_dir.resolve()}:/output" 
        -B "{license.resolve()}:/license.txt" 
        --pwd /
        docker://deepmi/fastsurfer:{tag} /fastsurfer/run_fastsurfer.sh
        --fs_license /license.txt 
        --t1 /data/{t1_name}
        --sid {subject}
        --sd /output 
        --threads {threads}
        {"--viewagg_device 'cpu'" * (use_cpu)}
        --no_hypothal
        --3T
    """
    subprocess.run(shlex.split(cmd), check=True)


if __name__ == "__main__":
    run_fastsurfer()
