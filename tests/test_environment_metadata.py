from pathlib import Path
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT.parent / "gmri2fem"


def load_toml(path):
    with path.open("rb") as stream:
        return tomllib.load(stream)


def editable_examples():
    documentation = (ROOT / "docs/environment-release.md").read_text()
    section = documentation.split("## Editable development", 1)[1].split("## Conda fallback", 1)[0]
    snippets = section.split("```toml\n")
    return [tomllib.loads(snippet.split("```", 1)[0]) for snippet in snippets[1:]]


class EnvironmentMetadataTests(unittest.TestCase):
    def setUp(self):
        self.pixi = load_toml(ROOT / "pixi.toml")

    def test_root_manifest_layout(self):
        self.assertEqual(self.pixi["dependencies"]["python"], ">=3.11,<3.12")
        self.assertEqual(self.pixi["dependencies"]["gmri2fem-fsl"], "==0.1.0")
        self.assertNotIn("pypi-dependencies", self.pixi)
        self.assertNotIn("feature", self.pixi)
        self.assertIn("docs-build", self.pixi["tasks"])

    def test_shared_dependencies_exclude_gmri2fem_stack(self):
        shared = set(self.pixi["dependencies"])
        self.assertFalse(shared & {"panta-rhei", "gmri2fem", "simple-mri", "setuptools"})

    def test_root_lock_has_no_local_paths(self):
        lock = (ROOT / "pixi.lock").read_text()
        self.assertNotIn("../gmri2fem", lock)
        self.assertNotIn("file://", lock)
        self.assertIn("jorgenriseth/noarch/gmri2fem-0.3.1-", lock)

    def test_editable_examples(self):
        native, editable = editable_examples()
        self.assertNotIn("gmri2fem-fsl", native)
        self.assertEqual(editable["pypi-dependencies"]["gmri2fem"],
                         {"path": "../gmri2fem", "editable": True})


@unittest.skipUnless(LIBRARY.is_dir(), "requires sibling gmri2fem checkout")
class LibraryDriftTests(unittest.TestCase):
    def test_documented_editable_requirements_match_library(self):
        documented, _ = editable_examples()
        fsl = load_toml(LIBRARY / "conda-recipe/fsl.toml")["dependencies"]
        mapping = load_toml(LIBRARY / "conda-recipe/dependencies.toml")
        for name, constraint in {**fsl, **mapping["native"]}.items():
            self.assertEqual(documented[name], constraint, name)
        for requirement in (mapping["overrides"]["pyvista[all]"][0], mapping["overrides"]["vtk"][0]):
            name, _, constraint = requirement.partition(" ")
            self.assertEqual(documented[name], constraint, name)


if __name__ == "__main__":
    unittest.main()
