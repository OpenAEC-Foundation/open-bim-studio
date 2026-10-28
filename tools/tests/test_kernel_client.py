"""kernel_client.py writes the client wrappers for the exposed functions of a
library file: the same patterns, each calling the compiler's C symbol. The
fixture holds four exposed functions whose symbols were read with llvm-nm
from an object the compiler produced; the golden file must come out exactly."""
import pathlib
import subprocess
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
TOOLS = HERE.parent
FIXTURE = HERE / "kernel_client_fixture"


def normalised(text):
    return text.replace("\r\n", "\n")


class KernelClientTest(unittest.TestCase):
    def test_exposed_functions_produce_the_golden_client(self):
        with tempfile.TemporaryDirectory() as out:
            target = pathlib.Path(out) / "client.dl"
            subprocess.run(
                [sys.executable, "-B", str(TOOLS / "kernel_client.py"),
                 "--exposed", str(FIXTURE / "exposed.dl"), "--out", str(target)],
                check=True)
            got = target.read_text(encoding="utf-8")
            want = (FIXTURE / "expected_client.dl").read_text(encoding="utf-8")
            self.assertEqual(normalised(got), normalised(want))

    def test_the_committed_client_is_current(self):
        root = TOOLS.parent
        result = subprocess.run(
            [sys.executable, "-B", str(TOOLS / "kernel_client.py"), "--check",
             "--exposed", str(root / "kernel" / "api" / "exposed.dl"), "--out", str(root / "kernel" / "api" / "client.dl")],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
