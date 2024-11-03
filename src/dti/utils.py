import json
import subprocess
from pathlib import Path

import click


def mri_number_of_frames(input: Path) -> int:
    return int(
        subprocess.check_output(
            f"mri_info --nframes {input} | grep -v INFO", shell=True
        )
    )


def readout_time(sidecar: Path) -> str:
    print(sidecar)
    with open(sidecar, "r") as f:
        meta = json.load(f)
    return meta["EstimatedTotalReadoutTime"]


def with_suffix(p: Path, newsuffix: str) -> Path:
    assert "." in newsuffix, "invalid suffix"
    return p.parent / f"{p.name.split('.')[0]}{newsuffix}"


@click.command("eddy-index")
@click.option("--input", type=Path, required=True)
@click.option("--output", type=Path, required=True)
def create_eddy_index_file(input: Path, output: Path):
    index = ["1"] * mri_number_of_frames(input)
    with open(output, "w") as f:
        f.write(" ".join(index))


@click.command("topup-params")
@click.option("--imain", type=Path, required=True)
@click.option("--b0_topup", type=Path, required=True)
@click.option("--output", type=Path, required=True)
def create_topup_params_file(imain: Path, b0_topup: Path, output: Path):
    nframes = mri_number_of_frames(str(imain).replace("DTI.nii.gz", "b0.nii.gz"))
    print(str(imain).replace("DTI.nii.gz", "b0.nii.gz"))
    print(nframes)
    main_readout_time = readout_time(with_suffix(imain, ".json"))
    topup_readout_time = readout_time(with_suffix(b0_topup, ".json"))
    with open(output, "w") as f:
        for i in range(nframes):
            f.write(f"0 -1 0 {main_readout_time}\n")
        f.write(f"0 1 0 {topup_readout_time}\n")
