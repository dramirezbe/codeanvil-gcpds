"""Check captured file bytes, executable flags and relative links; writes nothing."""

import hashlib
import json
import os
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parent
    manifest = json.loads((root / "ARCHIVE_MANIFEST.json").read_text(encoding="utf-8"))
    failures = []
    for entry in manifest["entries"]:
        path = root / entry["path"]
        if entry["type"] == "symlink":
            valid = path.is_symlink() and os.readlink(path) == entry["target"]
            valid = valid and path.exists() and path.resolve().is_relative_to(root)
        else:
            valid = path.is_file() and not path.is_symlink()
            if valid:
                valid = hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"]
                if os.name != "nt":
                    valid = valid and bool(path.stat().st_mode & 0o111) == entry["executable"]
        if not valid:
            failures.append(entry["path"])
    if failures:
        print("Archive mismatch:\n" + "\n".join(failures))
        return 1
    print(f"PASS: {len(manifest['projects'])} projects, {len(manifest['entries'])} captured entries.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
