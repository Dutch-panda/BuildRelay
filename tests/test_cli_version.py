from pathlib import Path
import subprocess
import sys
from contracts import __version__

MAIN_PY = str(Path(__file__).resolve().parent.parent / "main.py")


def test_cli_version_flag():
    res = subprocess.run(
        [sys.executable, MAIN_PY, "--version"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert f"buildrelay {__version__}" in res.stdout or f"buildrelay {__version__}" in res.stderr


def test_cli_version_short_flag():
    res = subprocess.run(
        [sys.executable, MAIN_PY, "-V"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert f"buildrelay {__version__}" in res.stdout or f"buildrelay {__version__}" in res.stderr
