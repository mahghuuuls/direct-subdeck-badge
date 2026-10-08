"""Build and validate the Direct Subdeck Badge .ankiaddon archive."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "dist" / "direct-subdeck-badge.ankiaddon"
PACKAGE_FILES = (
    "__init__.py",
    "config.json",
    "config.md",
    "manifest.json",
    "README.md",
    "CHANGELOG.md",
    "LICENSE",
)
REQUIRED_MANIFEST_KEYS = ("package", "name")


def validate_source() -> None:
    missing = [name for name in PACKAGE_FILES if not (ROOT / name).is_file()]
    if missing:
        raise SystemExit(f"Missing package files: {', '.join(missing)}")

    try:
        manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as error:
        raise SystemExit(f"Invalid package metadata: {error}") from error

    missing_keys = [key for key in REQUIRED_MANIFEST_KEYS if not manifest.get(key)]
    if missing_keys:
        raise SystemExit(f"manifest.json is missing values for: {', '.join(missing_keys)}")


def build() -> None:
    validate_source()
    OUTPUT.parent.mkdir(exist_ok=True)

    with zipfile.ZipFile(OUTPUT, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in PACKAGE_FILES:
            archive.write(ROOT / name, arcname=name)

    with zipfile.ZipFile(OUTPUT) as archive:
        actual = tuple(archive.namelist())
        if actual != PACKAGE_FILES:
            raise SystemExit(f"Unexpected archive contents: {actual!r}")
        if archive.testzip() is not None:
            raise SystemExit("The generated archive failed its CRC check")

    print(f"Built {OUTPUT.relative_to(ROOT)}")
    print("Archive contents:")
    for name in PACKAGE_FILES:
        print(f"  {name}")


if __name__ == "__main__":
    build()
