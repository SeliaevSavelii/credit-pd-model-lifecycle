"""Reproduce the whole project: tests -> data download/extract -> notebooks 01-05 in order.

Usage:
    python run_all.py                         # execute notebooks in place
    python run_all.py --output-dir /tmp/run   # write executed copies elsewhere
    python run_all.py --html                  # also export reports/html/*.html
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

import nbformat
from nbclient import NotebookClient
from nbconvert import HTMLExporter

from src.data_prep import download, extract

ROOT = Path(__file__).resolve().parent
NOTEBOOKS = sorted((ROOT / "notebooks").glob("0[1-5]_*.ipynb"))


def run_notebook(path: Path, output_dir: Path, html_dir: Path | None) -> None:
    nb = nbformat.read(path, as_version=4)
    NotebookClient(
        nb, kernel_name="python3", timeout=1800, resources={"metadata": {"path": str(path.parent)}},
    ).execute()
    nbformat.write(nb, output_dir / path.name)
    if html_dir is not None:
        body, _ = HTMLExporter().from_notebook_node(nb)
        (html_dir / path.with_suffix(".html").name).write_text(body, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "notebooks")
    parser.add_argument("--html", action="store_true")
    parser.add_argument("--skip-tests", action="store_true")
    args = parser.parse_args()

    if not args.skip_tests:
        subprocess.run([sys.executable, "-m", "pytest", "-q", "tests"], cwd=ROOT, check=True)

    print("raw data:", download())
    print("extract:", extract(force=True))

    args.output_dir.mkdir(parents=True, exist_ok=True)
    html_dir = None
    if args.html:
        html_dir = ROOT / "reports" / "html"
        html_dir.mkdir(parents=True, exist_ok=True)

    for path in NOTEBOOKS:
        start = time.time()
        run_notebook(path, args.output_dir, html_dir)
        print(f"executed {path.name} in {time.time() - start:.0f}s")


if __name__ == "__main__":
    main()
