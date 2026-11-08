import importlib.util
from pathlib import Path
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT.parent / "gmri2fem"
spec = importlib.util.spec_from_file_location("prepare_environment", ROOT / "scripts/prepare_environment.py")
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)


class EnvironmentMetadataTests(unittest.TestCase):
    def setUp(self):
        self.pixi = prepare.load(ROOT / "pixi.toml")
        self.feature = self.pixi["feature"]["gmri2fem-dev"]

    def test_root_manifest_layout(self):
        project = prepare.load(ROOT / "pyproject.toml")
        self.assertNotIn("pixi", project.get("tool", {}))
        self.assertEqual(self.pixi["dependencies"]["python"], project["project"]["requires-python"])
        self.assertEqual(self.pixi["environments"]["default"], ["gmri2fem-dev"])
        self.assertEqual(
            self.feature["pypi-dependencies"]["gmri2fem"],
            {"path": "../gmri2fem/", "editable": True},
        )
        self.assertNotIn("pypi-dependencies", self.pixi)
        self.assertIn("docs-build", self.pixi["tasks"])

    def test_shared_dependencies_exclude_gmri2fem_stack(self):
        shared = set(self.pixi["dependencies"])
        self.assertFalse(shared & set(self.feature["dependencies"]))
        self.assertFalse(shared & {"panta-rhei", "gmri2fem", "simple-mri", "setuptools"})

    def test_roundtrip(self):
        data = {"workspace": {"name": "test", "channels": ["conda-forge"]},
                "pypi-dependencies": {"example": {"path": "/tmp/example", "editable": True}}}
        self.assertEqual(tomllib.loads("\n".join(prepare.dump_tables(data))), data)

    def test_release_manifest_has_no_local_paths(self):
        data = prepare.load(ROOT / "envs/release/pixi.toml")
        self.assertIn("gmri2fem-fsl", data["dependencies"])
        self.assertNotIn("pypi-dependencies", data)
        self.assertNotIn("feature", data)
        self.assertFalse(set(data["dependencies"]) & set(self.feature["dependencies"]))
        self.assertEqual(data["dependencies"]["python"], ">=3.11,<3.12")


@unittest.skipUnless(LIBRARY.is_dir(), "requires sibling gmri2fem checkout")
class LibraryDriftTests(unittest.TestCase):
    def setUp(self):
        self.feature = prepare.load(ROOT / "pixi.toml")["feature"]["gmri2fem-dev"]["dependencies"]

    def test_release_manifest_is_current(self):
        data = prepare.manifest(LIBRARY)
        self.assertEqual(data, prepare.load(ROOT / "envs/release/pixi.toml"))

    def test_development_feature_matches_library_policies(self):
        fsl = prepare.load(LIBRARY / "conda-recipe/fsl.toml")["dependencies"]
        native = prepare.load(LIBRARY / "conda-recipe/dependencies.toml")["native"]
        for name, constraint in {**fsl, **native}.items():
            self.assertEqual(self.feature.get(name), constraint, name)


if __name__ == "__main__":
    unittest.main()
