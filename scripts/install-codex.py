#!/usr/bin/env python3
"""Install the Claude + Codex loop files without replacing project customizations."""

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

SOURCE = Path(__file__).resolve().parents[1]


def source_files():
    paths = list((SOURCE / ".claude").rglob("*"))
    paths += list((SOURCE / ".agents/skills").rglob("SKILL.md"))
    paths += list((SOURCE / ".codex/agents").glob("*.toml"))
    paths += [SOURCE / ".codex/LOOP.md", SOURCE / ".codex/hooks/loop.py", SOURCE / "scripts/check-codex-branch.py"]
    return sorted(path for path in paths if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc")


def check_path(destination, relative):
    path = destination
    for part in relative.parts:
        path = path / part
        if path.is_symlink():
            raise ValueError(f"Refusing symlink in installation path: {path}")
        if path.exists() and path != destination / relative and not path.is_dir():
            raise ValueError(f"Expected directory: {path}")
    return path


def merged_hooks(destination, migrate=False):
    path = check_path(destination, Path(".codex/hooks.json"))
    wanted = json.loads((SOURCE / ".codex/hooks.json").read_text())
    current = json.loads(path.read_text()) if path.exists() else {"hooks": {}}
    if not isinstance(current, dict) or not isinstance(current.get("hooks", {}), dict):
        raise ValueError("Existing .codex/hooks.json has an invalid hooks object")
    config = check_path(destination, Path(".codex/config.toml"))
    if config.exists() and ".codex/hooks/loop.py" in config.read_text():
        raise ValueError("Loop hooks already appear in config.toml; resolve duplicate registration before installing")
    events = current.setdefault("hooks", {})
    for event, entries in wanted["hooks"].items():
        existing = events.setdefault(event, [])
        if not isinstance(existing, list):
            raise ValueError(f"Existing {event} hooks are not an array")
        for entry in entries:
            legacy = json.loads(json.dumps(entry))
            legacy["hooks"][0]["command"] = 'python3 "$(git rev-parse --show-toplevel)/.codex/hooks/loop.py"'
            recognized = [entry, legacy] if migrate else [entry]
            if any(".codex/hooks/loop.py" in json.dumps(item) and item not in recognized
                   for item in existing):
                raise ValueError(f"Conflicting existing loop hook for {event}")
            if entry in existing:
                if migrate:
                    existing[:] = [item for item in existing if item != legacy]
                continue
            if migrate and legacy in existing:
                existing[existing.index(legacy)] = entry
                continue
            if any(".codex/hooks/loop.py" in json.dumps(item) for item in existing):
                raise ValueError(f"Conflicting existing loop hook for {event}")
            existing.append(entry)
    return path, (json.dumps(current, indent=2) + "\n").encode()


def install(destination, dry_run=False):
    destination = destination.resolve()
    actual = subprocess.run(["git", "-C", str(destination), "rev-parse", "--show-toplevel"],
                            capture_output=True, text=True, check=True)
    if Path(actual.stdout.strip()).resolve() != destination:
        raise ValueError("Destination must be the root of an existing Git repository")
    if destination == SOURCE:
        raise ValueError("Install into an adopting project, not the template checkout")
    writes = []
    installed = []
    # Check every collision before writing anything, including hook configuration.
    for source in source_files():
        relative = source.relative_to(SOURCE)
        target = check_path(destination, relative)
        data = source.read_bytes()
        if target.exists():
            if not target.is_file() or target.read_bytes() != data:
                raise ValueError(f"Conflicting file: {relative}. Preserve it and resolve the collision before installing.")
        else:
            writes.append((target, data))
        installed.append(str(relative))
    hook_path, hook_data = merged_hooks(destination)
    backup_path = check_path(destination, Path(".codex/hooks.json.before-loop"))
    if backup_path.exists() and not backup_path.is_file():
        raise ValueError("Expected a regular hook backup file")
    if not hook_path.exists() or json.loads(hook_path.read_text()) != json.loads(hook_data):
        writes.append((hook_path, hook_data))
    record_path = check_path(destination, Path(".codex/loop-installed.json"))
    record = (json.dumps({"source": "https://github.com/DanielMJ511/loop-template-codex",
                          "files": installed + [".codex/hooks.json"]}, indent=2) + "\n").encode()
    if record_path.exists() and record_path.read_bytes() != record:
        raise ValueError("Conflicting .codex/loop-installed.json; review the earlier installation before replacing it")
    if not record_path.exists():
        writes.append((record_path, record))
    print(f"{'Would write' if dry_run else 'Writing'} {len(writes)} files in {destination}")
    for path, data in writes:
        print(path.relative_to(destination))
    if dry_run:
        return
    for path, data in writes:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path == hook_path and path.exists():
            # Preserve the exact original before the only merge this installer performs.
            if not backup_path.exists():
                shutil.copy2(path, backup_path)
        path.write_bytes(data)
    print("Installed. Start Codex, review project hooks in /hooks, then invoke $loop-init.")
    print("No loop state or global settings were changed. Re-run with --dry-run to check collisions.")


def migrate_hooks(destination, dry_run=False):
    destination = destination.resolve()
    actual = subprocess.run(["git", "-C", str(destination), "rev-parse", "--show-toplevel"],
                            capture_output=True, text=True, check=True)
    if Path(actual.stdout.strip()).resolve() != destination:
        raise ValueError("Destination must be the repository root")
    path, data = merged_hooks(destination, migrate=True)
    backup = check_path(destination, Path(".codex/hooks.json.before-recovery"))
    if backup.exists() and not backup.is_file():
        raise ValueError("Expected a regular backup file")
    if path.exists() and path.read_bytes() == data:
        print("Hooks already current")
        return
    print("Would migrate hooks" if dry_run else "Migrating hooks; review/trust in /hooks before use")
    if not dry_run:
        if path.exists() and not backup.exists():
            shutil.copy2(path, backup)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--migrate-hooks", action="store_true", help="Migrate exact legacy hook definitions only")
    args = parser.parse_args()
    try:
        (migrate_hooks if args.migrate_hooks else install)(args.destination, args.dry_run)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        sys.exit(str(error))


if __name__ == "__main__":
    main()
