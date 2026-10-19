"""Rebuild the selected cuboid models and render their Blender previews."""

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
subprocess.run(
    ["python3", str(ROOT / "tools/make_models.py"), "--group", "dish"],
    check=True,
    cwd=ROOT,
)
from blender_preview import render

render("dish")
