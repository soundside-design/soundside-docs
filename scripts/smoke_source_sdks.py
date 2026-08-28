#!/usr/bin/env python3
"""Hermetic source-package build/install/import smoke for both SDKs."""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*args: str, cwd: Path, env=None) -> None:
    subprocess.run(args, cwd=cwd, env=env, check=True)


def copy_source(source: Path, target: Path) -> None:
    shutil.copytree(source, target, ignore=shutil.ignore_patterns("dist", "build", "node_modules", "*.egg-info", "__pycache__"))


def smoke_python(temp: Path) -> None:
    source = temp / "python-sdk"
    copy_source(ROOT / "sdks/python", source)
    venv = temp / "python-build-venv"
    run(sys.executable, "-m", "venv", str(venv), cwd=temp)
    python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    run(str(python), "-m", "pip", "install", "build", cwd=temp)
    output = temp / "python-artifacts"
    run(str(python), "-m", "build", "--outdir", str(output), str(source), cwd=temp)
    wheels = list(output.glob("*.whl"))
    sdists = list(output.glob("*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        raise RuntimeError("Python smoke must build exactly one wheel and one sdist")
    consumer = temp / "python-consumer-venv"
    run(sys.executable, "-m", "venv", str(consumer), cwd=temp)
    consumer_python = consumer / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    run(str(consumer_python), "-m", "pip", "install", str(wheels[0]), cwd=temp)
    run(str(consumer_python), "-c", "from soundside import Soundside; assert Soundside", cwd=temp)


def smoke_typescript(temp: Path) -> None:
    source = temp / "typescript-sdk"
    copy_source(ROOT / "sdks/typescript", source)
    npm_env = {**os.environ, "NPM_CONFIG_CACHE": str(temp / "npm-cache")}
    run("npm", "ci", cwd=source, env=npm_env)
    run("npm", "run", "build", cwd=source, env=npm_env)
    pack_output = subprocess.check_output(["npm", "pack", "--json", "--pack-destination", str(temp)], cwd=source, env=npm_env, text=True)
    import json
    tarball = temp / json.loads(pack_output)[0]["filename"]
    consumer = temp / "typescript-consumer"
    consumer.mkdir()
    run("npm", "init", "-y", cwd=consumer, env=npm_env)
    run("npm", "install", str(tarball), cwd=consumer, env=npm_env)
    run("node", "--input-type=module", "-e", "import { Soundside } from 'soundside'; if (!Soundside) process.exit(1)", cwd=consumer, env=npm_env)


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--python", action="store_true")
    group.add_argument("--typescript", action="store_true")
    args = parser.parse_args()
    before = subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=all"], cwd=ROOT, text=True)
    with tempfile.TemporaryDirectory(prefix="soundside-sdk-smoke-") as directory:
        temp = Path(directory)
        smoke_python(temp) if args.python else smoke_typescript(temp)
    after = subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=all"], cwd=ROOT, text=True)
    if after != before:
        raise RuntimeError("SDK smoke changed repository output")
    print("source SDK smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
