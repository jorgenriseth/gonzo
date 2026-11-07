# Environment migration and local release rehearsal

The root `pixi.toml` and `pixi.lock` deliberately retain the existing
editable development setup during this migration. Python package metadata
remains separately in `pyproject.toml`; Pixi no longer reads its dependencies
implicitly. The manifest explicitly preserves those environment requirements.
No packages or images have
been uploaded. The public channel currently has gmri2fem 0.2.8 and no
`gmri2fem-fsl`; changing the default now would break installation.

The generated [release candidate](../envs/release/pixi.toml) selects the new
companion, keeps Gonzo's scientific compatibility caps, and requires Python
3.11. It has no sibling checkout dependency. Do not treat it as promoted until
the steps below succeed.

Local resolution, installation, CLI/native smoke checks, and the fixture DAG
have succeeded against locally built packages. Publication remains blocked by
the Gmsh Python-metadata mismatch reported by gmri2fem's strict `pip check` gate.
No checker exception or panta-rhei removal is included in this migration.
The portable release lock, replacement default/fallback, and container
promotion remain deferred.

## Local release environment

First build the library and companion locally using gmri2fem's
[release instructions](https://github.com/jorgenriseth/gMRI2FEM/blob/main/docs/releases.md).
With the sibling repositories checked out, run from Gonzo:

```bash
python3 scripts/prepare_environment.py \
  --channel ../gmri2fem/dist/conda \
  --output envs/rehearsal/pixi.toml
pixi lock --manifest-path envs/rehearsal/pixi.toml
pixi install --manifest-path envs/rehearsal/pixi.toml --locked --run-post-link-scripts
pixi run --manifest-path envs/rehearsal/pixi.toml --locked \
  python scripts/validate_environment.py
```

Use Pixi 0.83.0. The rehearsal lock refers to a local channel and is not a
portable release lock. Do not commit it. The generator reads FSL requirements
from gmri2fem's authoritative policy; it does not duplicate their constraints.

The checks exercise CLI loading, native mesh operations, FSL prerequisites,
and a data-free reference-image DAG from the actual Snakefile. They do not
establish full-pipeline numerical equivalence. Compare representative real
outputs before approving promotion, particularly DTI reorientation and
downstream tensor/mesh products relative to the 0.2.8 container.

## Independent editable environment

```bash
python3 scripts/prepare_environment.py --development \
  --output envs/development/pixi.toml
pixi install --manifest-path envs/development/pixi.toml --run-post-link-scripts
```

This uses the sibling checkout and FSL requirements generated from the same
policy. It does not install the companion, which would pull a released copy
of gmri2fem into the editable environment. Local paths and locks stay out of
the default release environment.

## Promotion after explicit publication approval

1. Publish the tested library/companion artifacts only after reviewing their
   tests and obtaining approval.
2. Generate the canonical manifest without a local channel:

   ```bash
   python3 scripts/prepare_environment.py --output envs/release/pixi.toml
   pixi lock --manifest-path envs/release/pixi.toml
   pixi install --manifest-path envs/release/pixi.toml --locked --run-post-link-scripts
   pixi run --manifest-path envs/release/pixi.toml --locked \
     python scripts/validate_environment.py
   pixi workspace export conda-environment \
     --manifest-path envs/release/pixi.toml --from-lock-file envs/gonzo.yml
   ```

3. Commit the canonical manifest, portable lock, and generated Conda fallback
   together. Verify the resolved gmri2fem version/build and absence of editable
   paths. The current fallback YAML remains legacy until this promotion.
4. Promote the release configuration to root `pixi.toml` and update default
   installation instructions in the same adoption
   change, removing handwritten FSL pins and selecting the companion.
   The environment workflow is manual-only until the portable release lock
   exists; enable PR validation at that point.
5. Test the container and representative real-data outputs before distributing
   a new image. Record the Gonzo commit, package versions, lock checksum, image
   digest, and Greedy version.

To check manifest drift while both repositories are available:

```bash
python3 scripts/prepare_environment.py --output envs/release/pixi.toml --check
python3 -m unittest discover -s tests -p 'test_environment_metadata.py'
```

Conda's exported YAML is a convenience installation route; the Pixi lock
records more precise artifact identities. Never hand-edit either generated file.

## Container

The Dockerfile now requires the promoted release manifest and lock, and pins
the Pixi base image to the version that matches the lock format. Greedy is downloaded from SourceForge's nightly
URL as before, so it is not pinned: record the version printed by
`greedy -version` for each built image.

```bash
docker build -f docker/Dockerfile -t gonzo:rehearsal .
```

Image construction runs non-root environment
smoke tests. Do not update the existing SIF or pipeline container reference
until those tests and real-data validation pass. Fetch images by immutable
tag/digest rather than assuming today's `latest` matches an existing SIF.

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
