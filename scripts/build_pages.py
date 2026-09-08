import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
SITE = ROOT / "_site"
DOWNLOAD = ROOT / "_download"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def run(command):
    subprocess.run(command, cwd=ROOT, check=True)


def safe_extract(archive_path: Path, destination: Path):
    destination = destination.resolve()
    with zipfile.ZipFile(archive_path, "r") as archive:
        for item in archive.infolist():
            target = (destination / item.filename).resolve()
            if destination != target and destination not in target.parents:
                raise RuntimeError(f"Unsafe archive path: {item.filename}")
        archive.extractall(destination)


def copy_public():
    for source in PUBLIC.rglob("*"):
        relative = source.relative_to(PUBLIC)
        target = SITE / relative
        if source.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)


def deploy_player(release: str):
    safe_release = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in release)
    expected_name = f"webgl-player-{safe_release}.zip"
    fixture = os.environ.get("WEBGL_RELEASE_ASSET_DIR", "").strip()
    if fixture:
        source = Path(fixture) / expected_name
        if not source.is_file():
            raise RuntimeError(f"Missing WebGL Player archive: {expected_name}")
        shutil.copy2(source, DOWNLOAD / expected_name)
    else:
        run([
            "gh", "release", "download", release,
            "--repo", os.environ["GITHUB_REPOSITORY"],
            "--dir", str(DOWNLOAD),
            "--clobber",
            "--pattern", expected_name,
        ])

    archive = DOWNLOAD / expected_name
    if not archive.is_file():
        raise RuntimeError(f"Release {release} does not contain {expected_name}")
    safe_extract(archive, SITE)


def main():
    runtime = load_json(PUBLIC / "control" / "runtime.json")
    if SITE.exists():
        shutil.rmtree(SITE)
    if DOWNLOAD.exists():
        shutil.rmtree(DOWNLOAD)
    SITE.mkdir(parents=True)
    DOWNLOAD.mkdir(parents=True)

    copy_public()
    release = str(runtime.get("activeRelease", "")).strip()
    if release:
        deploy_player(release)
    (SITE / ".nojekyll").write_text("", encoding="utf-8")
    shutil.rmtree(DOWNLOAD, ignore_errors=True)
    print(f"Pages artifact ready: release={release or 'none'}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
