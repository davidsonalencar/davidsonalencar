#!/usr/bin/env python3
"""Copy the WakaTime stats block from README.md into the translated READMEs.

The waka-readme-stats action only ever rewrites the repository's canonical
README (`GitHubManager.REMOTE.get_readme().path`, i.e. README.md) — there is no
target-file input. Without this step the translations would keep whatever
numbers they were committed with.

Run from the repository root. Exits non-zero only on a real error; "nothing
changed" is a success.
"""

from pathlib import Path
from re import DOTALL, escape, search, sub
from sys import exit, stderr

SOURCE = Path("README.md")
TARGETS = [Path("README.pt-BR.md"), Path("README.es.md")]

START = "<!--START_SECTION:waka-->"
END = "<!--END_SECTION:waka-->"
BLOCK = f"{escape(START)}.*?{escape(END)}"


def read_block(path: Path) -> str:
    match = search(BLOCK, path.read_text(encoding="utf-8"), DOTALL)
    if match is None:
        print(f"{path}: no {START} … {END} section found", file=stderr)
        exit(1)
    return match.group(0)


def main() -> None:
    block = read_block(SOURCE)
    changed = []

    for target in TARGETS:
        if not target.exists():
            print(f"{target}: missing, skipped", file=stderr)
            continue

        contents = target.read_text(encoding="utf-8")
        read_block(target)  # fail loudly if the markers were dropped
        updated = sub(BLOCK, lambda _: block, contents, count=1, flags=DOTALL)

        if updated != contents:
            target.write_text(updated, encoding="utf-8")
            changed.append(str(target))

    print(f"Synced: {', '.join(changed)}" if changed else "Already in sync.")


if __name__ == "__main__":
    main()
