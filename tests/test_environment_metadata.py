import importlib.util
from pathlib import Path
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("prepare_environment", ROOT / "scripts/prepare_environment.py")
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)


class EnvironmentMetadataTests(unittest.TestCase):
    def test_separate_pixi_manifest_preserves_default(self):
        project = prepare.load(ROOT / "pyproject.toml")
        data = prepare.load(ROOT / "pixi.toml")
        self.assertNotIn("pixi", project.get("tool", {}))
        self.assertEqual(data["dependencies"]["python"], project["project"]["requires-python"])
        self.assertEqual(data["pypi-dependencies"]["simple-mri"], ">=0.1.6,<0.2")
        self.assertEqual(
            data["pypi-dependencies"]["gmri2fem"],
            {"path": "../gmri2fem/", "editable": True},
        )
        self.assertIn("docs-build", data["tasks"])

    def test_generator_uses_root_pixi_manifest(self):
        data = prepare.manifest(ROOT.parent / "gmri2fem")
        release_data = prepare.load(ROOT / "envs/release/pixi.toml")
        self.assertEqual(data["dependencies"], release_data["dependencies"])
        self.assertIn("gmri2fem-fsl", data["dependencies"])
        self.assertFalse(data["pypi-dependencies"])

    def test_roundtrip(self):
        data = {"workspace": {"name": "test", "channels": ["conda-forge"]},
                "pypi-dependencies": {"example": {"path": "/tmp/example", "editable": True}}}
        self.assertEqual(tomllib.loads("\n".join(prepare.dump_tables(data))), data)

    def test_release_manifest_has_no_local_paths(self):
        path = ROOT / "envs/release/pixi.toml"
        data = prepare.load(path)
        self.assertIn("gmri2fem-fsl", data["dependencies"])
        self.assertNotIn("gmri2fem", data.get("pypi-dependencies", {}))
        self.assertNotIn("fsl-eddy", data["dependencies"])
        self.assertEqual(data["dependencies"]["python"], ">=3.11,<3.12")


if __name__ == "__main__":
    unittest.main()
