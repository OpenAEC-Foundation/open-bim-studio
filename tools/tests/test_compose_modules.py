"""compose_modules.py writes the model record and the dispatchers from the
MODULE manifests it finds under a root; two fixture manifests must produce
exactly the golden files beside them."""
import pathlib
import subprocess
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
TOOLS = HERE.parent
FIXTURE = HERE / "compose_fixture"


def normalised(text):
    return text.replace("\r\n", "\n")


class ComposeModulesTest(unittest.TestCase):
    def test_two_manifests_produce_the_golden_files(self):
        with tempfile.TemporaryDirectory() as out:
            subprocess.run(
                [sys.executable, "-B", str(TOOLS / "compose_modules.py"),
                 "--root", str(FIXTURE), "--out", out],
                check=True)
            for name in ("model.dl", "compose.dl"):
                got = (pathlib.Path(out) / name).read_text(encoding="utf-8")
                want = (FIXTURE / f"expected_{name}").read_text(encoding="utf-8")
                self.assertEqual(normalised(got), normalised(want), name)


if __name__ == "__main__":
    unittest.main()
