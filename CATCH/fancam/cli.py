from __future__ import annotations

import argparse
from pathlib import Path

from .models import Project
from .processor import process_project


def main() -> None:
    parser = argparse.ArgumentParser(description="Fancam Maker rendering engine")
    parser.add_argument("project", help=".fancam.json project file")
    parser.add_argument("--output", required=True, help="MP4 output path")
    args = parser.parse_args()
    project = Project.load(args.project)
    result = process_project(project, Path(args.output), lambda n, total: print(f"{n}/{total}", flush=True))
    print(result.output)


if __name__ == "__main__":
    main()
