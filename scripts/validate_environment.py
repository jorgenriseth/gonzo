"""Data-free checks for a released or editable Gonzo execution environment."""

from importlib.metadata import version
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


def main():
    import dolfin as df
    import numpy as np
    import SVMTK
    import nibabel as nib
    from click.testing import CliRunner
    from _cli import gmri2fem
    from gmri2fem.concentration import concentration_from_T1

    print("gmri2fem:", version("gmri2fem"))
    for command in ["snakemake", "topup", "eddy", "dtifit", "bet", "fslroi", "fslmerge", "fslmaths"]:
        if shutil.which(command) is None:
            raise RuntimeError(f"Missing pipeline executable: {command}")
    if not (Path(os.environ["FSLDIR"]) / "etc/flirtsch/b02b0.cnf").is_file():
        raise RuntimeError("Missing FSL topup configuration")
    for args in [
        [], ["mri"], ["seg"], ["dti"], ["i2m"], ["brainmeshing"],
        ["i2m", "concentrations2mesh"], ["i2m", "dti2mesh"], ["i2m", "collect"],
        ["brainmeshing", "meshgen"], ["dti", "reslice-dti"],
    ]:
        result = CliRunner().invoke(gmri2fem, [*args, "--help"])
        if result.exit_code:
            raise RuntimeError(result.output) from result.exception
    mesh = df.UnitCubeMesh(2, 2, 2)
    assert np.isclose(df.assemble(df.Constant(1) * df.dx(domain=mesh)), 1)
    surface = SVMTK.Surface()
    surface.make_sphere(0, 0, 0, 1, 0.5)
    assert surface.num_vertices() > 0
    assert np.allclose(concentration_from_T1(np.array([1000.]), np.array([1000.]), .0032), 0)
    with tempfile.TemporaryDirectory() as directory:
        root = Path(__file__).resolve().parents[1]
        fixture = Path(directory)
        shutil.copy(root / "snakeconfig.yaml", fixture / "snakeconfig.yaml")
        (fixture / "build-record").mkdir()
        (fixture / "build-record/pipeline-leaf-files.txt").write_text("")
        source = fixture / "mri_dataset/sub-01/ses-01/anat/sub-01_ses-01_T1w.nii.gz"
        source.parent.mkdir(parents=True)
        nib.save(nib.Nifti1Image(np.ones((3, 3, 3)), np.eye(4)), source)
        subprocess.run([
            "snakemake", "--snakefile", str(root / "Snakefile"), "--directory", directory,
            "--cores", "1", "--dry-run",
            "mri_processed_data/sub-01/registered/sub-01_ses-01_T1w_registered.nii.gz",
        ], check=True)
    print("Environment smoke checks passed; no real MRI data were processed.")


if __name__ == "__main__":
    main()
