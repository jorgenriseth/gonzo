# Pipeline environments

The root `pixi.toml` and `pixi.lock` define the default pipeline environment.
It uses the published `gmri2fem-fsl` Conda companion, which installs a
compatible gmri2fem together with FEniCS, SVMTK, and the supported FSL stack.
The lock records the exact packages used by the default environment. The
environment does not require a sibling gmri2fem checkout.

Use Pixi 0.83.0 from the Gonzo repository:

```bash
pixi install --locked --run-post-link-scripts
pixi run --locked python scripts/validate_environment.py
```

The checks exercise CLI loading, native mesh operations, FSL prerequisites,
and a data-free reference-image DAG from the actual Snakefile. They do not
establish full-pipeline numerical equivalence. Compare representative real
outputs before approving promotion, particularly DTI reorientation and
downstream tensor/mesh products relative to the 0.2.8 container.

In a local installation, `fslchfiletype` and `fslchpixdim` were found with
interpreter paths from an older environment and shared hardlinks between
environments. Verify FSL Python wrappers in a clean installation with an
isolated package cache before relying on them or promoting a container.

## Editable development

To develop gmri2fem alongside Gonzo, check out gmri2fem as a sibling repository.
First save the current root manifest and lock, including any local changes:

```bash
backup_dir=$(mktemp -d)
cp -p pixi.toml pixi.lock "$backup_dir/"
printf 'Saved environment files in %s\n' "$backup_dir"
```

Temporarily remove `gmri2fem-fsl` from the root `[dependencies]` and add the
native and FSL requirements below to that same table. These values reflect the
current gmri2fem policies; check `conda-recipe/dependencies.toml` and
`conda-recipe/fsl.toml` in the sibling checkout for changes first.

```toml
fenics = ">=2019.2.0.dev20240219,<2020"
svmtk = ">=2.0.1,<3"
h5py = ">=3,<4"
pyvista = ">=0.44,<0.45"
vtk = "<9.4"
fsl-eddy = ">=2401.2,<2402"
fsl-topup = ">=2203.5,<2204"
fsl-fdt = ">=2202.11,<2203"
fsl-bet2 = ">=2111.8,<2112"
fsl-avwutils = "==2209.3"
```

Add this separate top-level table, adjusting the path if the checkout is not a
sibling. Do not retain `gmri2fem-fsl`: it would pull in the published library.

```toml
[pypi-dependencies]
gmri2fem = { path = "../gmri2fem", editable = true }
```

Resolve and validate the temporary environment:

```bash
pixi lock
pixi install --locked --run-post-link-scripts
pixi run --locked python scripts/validate_environment.py
```

This changes the root lock and installed default environment. Do not commit the
temporary manifest or lock. When finished, restore the saved files only after
checking for other changes made since the backup, then reinstall the released
environment:

```bash
cp -p "$backup_dir/pixi.toml" "$backup_dir/pixi.lock" .
pixi install --locked --run-post-link-scripts
```

## Conda fallback

The Conda YAML is an export of the root Pixi lock. Regenerate it after changing
the lock; do not edit it by hand:

```bash
pixi workspace export conda-environment --from-lock-file envs/gonzo.yml
conda env create -f envs/gonzo.yml
```

The Pixi lock records more precise artifact identities. Verify the Conda
environment and FSL activation separately before using this fallback.

## Local release rehearsal

First build the library and companion locally using gmri2fem's
[release instructions](https://github.com/jorgenriseth/gMRI2FEM/blob/main/README.md#contributors-and-release-maintainers).
Save the root manifest and lock as described above, then temporarily prepend
the absolute `file://` URL of `../gmri2fem/dist/conda` to the root workspace
channels. Set `gmri2fem-fsl` and `gmri2fem` in `[dependencies]` to the versions
of the locally built artifacts, so the intended library is selected even if the
companion supports multiple versions. Run the same lock, install, and
validation commands as above; inspect the lock to confirm both artifacts came
from the local channel. Restore the saved files and reinstall afterward. Do not
commit the local-channel manifest or lock.

## Container

The Dockerfile installs the root locked environment and runs non-root smoke
tests. Greedy is downloaded from SourceForge's nightly URL, so record the
version printed by `greedy -version` for each built image.

```bash
docker build -f docker/Dockerfile -t gonzo:rehearsal .
```

Image construction runs non-root environment
smoke tests. Do not update the existing SIF or pipeline container reference
until those tests and real-data validation pass. Fetch images by immutable
tag/digest rather than assuming today's `latest` matches an existing SIF.
Record the Gonzo commit, package versions, lock checksum, and image digest.

For inspection, avoid resolving the host's manifest through Apptainer:

```bash
apptainer exec --pwd /gonzo gonzo-pixi.sif \
  /gonzo/.pixi/envs/default/bin/python -c \
  "from importlib.metadata import version; print(version('gmri2fem'))"
```

FreeSurfer/FastSurfer setup and licensing remain external requirements.
The legacy `fenics2mri_workflow` still references an old source-checkout script
not shipped by the current package. That optional rule is an explicit adoption
blocker if needed; it must gain a tested installed interface before use.
