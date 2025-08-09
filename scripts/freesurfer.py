#!/usr/bin/env python3

import shlex
import subprocess
from pathlib import Path
from typing import Optional

import click


@click.command()
@click.option("-t1", type=Path, required=True)
@click.option("-o", "output", type=Path, required=True)
@click.option("-l", "license", type=Path, required=True)
@click.option("--flair", type=Path)
@click.option("--t2", type=Path)
@click.option("--threads", type=int, default=1)
@click.option("--version", type=str, default="7.4.1")
def run_freesurfer(
    t1: Path,
    output: Path,
    license: Path,
    flair: Optional[Path] = None,
    t2: Optional[Path] = None,
    version: str = "7.4.1",
    threads: int = 1,
):
    t1_dir = t1.parent
    fs_dir, subject = output.parent, output.name

    if (flair is not None) and (t2 is not None):
        raise RuntimeError("flair and t2 are mutually exclusive. Specify one.")

    t1_intermediate = f"/output/{subject}/mri/orig/001.mgz"
    if flair is not None:
        pial_intermediate = f"/output/{subject}/mri/orig/FLAIRraw.mgz"
        pial_setup = f"mri_convert --no_scale 1 /data/{flair.name}  {pial_intermediate}"
        pial_cmd = f"-FLAIRpial -FLAIR {pial_intermediate}"
    elif t2 is not None:
        pial_intermediate = f"/output/{subject}/mri/orig/T2raw.mgz"
        pial_setup = f"mri_convert -c --no_scale 1 /data/{t2.name}  {pial_intermediate}"
        pial_cmd = f"-T2pial -T2 {pial_intermediate}"
    else:
        pial_setup = ""
        pial_cmd = ""

    Path(f"{output}/mri/orig").mkdir(exist_ok=True, parents=True)
    singularity_cmd = f"""
        singularity exec -e
        --no-mount home,cwd 
        --cwd /
        -B "{t1_dir.resolve()}:/data" 
        -B "{fs_dir.resolve()}:/output" 
        -B "{license.resolve()}:/usr/local/freesurfer/.license"
        docker://freesurfer/freesurfer:{version}
    """
    t1_setup_cmd = f"mri_convert /data/{t1.name} {t1_intermediate}"
    recon_all_cmd = f"""
        recon-all 
        -all
        -sd /output 
        -s {subject}
        -threads {threads}
        -parallel
        {pial_cmd}
    """
    subprocess.run(shlex.split(singularity_cmd + t1_setup_cmd), check=True)
    if pial_setup:
        subprocess.run(shlex.split(singularity_cmd + pial_setup), check=True)

    subprocess.run(shlex.split(singularity_cmd + recon_all_cmd), check=True)


if __name__ == "__main__":
    run_freesurfer()
