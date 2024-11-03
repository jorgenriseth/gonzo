import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from dti.utils import mri_number_of_frames
import click


# TODO: Incorporate to allow multiple files resliced simultaneously
def moving_pair(args):
    assert len(args) == 2, f"Got {len(args)} arguments, should only have two"
    return f" -rm {args[0]} {args[1]} "


@click.command()
@click.option("--inpath", type=Path, required=True)
@click.option("--fixed", type=Path, required=True)
@click.option("--outpath", type=Path, required=True)
@click.option("--transform", type=Path)
@click.option("--threads", type=int, default=1)
def reslice4d(
    inpath: Path,
    fixed: Path,
    outpath: Path,
    transform: Optional[Path] = None,
    threads: int = 1,
) -> Path:
    if transform is None:
        transform = Path("")
    nframes = mri_number_of_frames(inpath)
    with tempfile.TemporaryDirectory(prefix=outpath.stem) as tmpdir:
        tmppath = Path(tmpdir)
        for i in range(nframes):
            tmp_split = tmppath / f"slice{i}.nii.gz"
            tmp_reslice = tmppath / f"reslice{i}.nii.gz"
            subprocess.run(
                f"fslroi {inpath} {tmp_split} {i} 1", shell=True
            ).check_returncode()
            subprocess.run(
                f"greedy -d 3 -rf {fixed} -rm {tmp_split} {tmp_reslice} -r {transform} -threads {threads}",
                shell=True,
            ).check_returncode()
        components = [str(tmppath / f"reslice{i}.nii.gz") for i in range(nframes)]
        subprocess.run(
            f"fslmerge -t {outpath} {' '.join(components)}", shell=True
        ).check_returncode()
    return outpath
