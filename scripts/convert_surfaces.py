import shlex
import subprocess
from pathlib import Path
from typing import Optional
from loguru import logger

import click


@click.command()
@click.option("-s", "fs_surface_dir", type=Path, required=True)
@click.option("-o", "output_dir", type=Path, required=True)
@click.option("-l", "license", type=Path, required=True)
@click.option("--suffix", type=str, default="")
@click.option("--verbose", type=bool, is_flag=True)
def run_fastsurfer(
    fs_surface_dir: Path,
    output_dir: Path,
    license: Path,
    suffix: Optional[str] = None,
    verbose: bool = False,
):
    suffix = "" if suffix is None else suffix
    singularity_cmd = f"""
        singularity exec -e
        --no-mount home,cwd 
        --cwd /
        -B "{fs_surface_dir.resolve()}:/data" 
        -B "{output_dir.resolve()}:/output" 
        -B "{license.resolve()}:/usr/local/freesurfer/.license"
        docker://freesurfer/freesurfer:7.4.1
    """

    fs_surfaces = ["rh.pial", "lh.pial", "rh.white", "lh.white"]
    logger.info("Converting FS-surfaces to .stl")
    for surface in fs_surfaces:
        input = f"/data/{surface}"
        output = Path(f"/output/{surface.replace('.', '_') + suffix}").with_suffix(
            ".stl"
        )
        redirect = ">> /dev/null" if not verbose else ""
        cmd = f"{singularity_cmd} mris_convert --to-scanner {input} {output} {redirect}"
        print(" ".join(shlex.split(cmd)))
        subprocess.run(
            " ".join(shlex.split(cmd)),
            shell=True,
        ).check_returncode()


if __name__ == "__main__":
    run_fastsurfer()
