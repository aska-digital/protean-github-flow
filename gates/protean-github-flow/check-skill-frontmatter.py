#!/usr/bin/env python3
"""check-skill-frontmatter.py - every shipped skill declares its contract.

For each `skills/*/SKILL.md`:

  1. a YAML frontmatter block exists and is closed;
  2. `name`, `description`, `version`, and `license` are present;
  3. `license` is MIT (the license this ingredient ships under);
  4. if an `author` field is present, it is one of the neutral authorship forms
     (the neutral attribution line, the engine authorship, or both). A personal
     name, a role codename, or a team name in that field is a leak.

Rule 4 is the attribution gate: a personal name, a role codename, or a team name
in a shipped skill's author field is a leak, so the fix has to change the file.

Usage: python3 gates/check-skill-frontmatter.py [path/to/repo]
Exit: 0 pass; 1 violation; 2 no skills found.
"""
import os
import re
import sys

ALLOWED_AUTHORS = (
    "the Protean publication",
    "the Protean publication, Hermes Agent",
    "Hermes Agent",
)
REQUIRED = ("name", "description", "version", "license")
SKILLS_DIR = "skills"


def frontmatter(text):
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    return text[3:end]


def main():
    repo = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
    if "--help" in sys.argv:
        print(__doc__.strip())
        return 0
    root = os.path.join(repo, SKILLS_DIR)
    if not os.path.isdir(root):
        print("gate error: no " + SKILLS_DIR + "/ directory")
        return 2
    violations = []
    scanned = 0
    for entry in sorted(os.listdir(root)):
        path = os.path.join(root, entry, "SKILL.md")
        if not os.path.isfile(path):
            continue
        scanned += 1
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        fm = frontmatter(text)
        rel = os.path.relpath(path, repo).replace(os.sep, "/")
        if fm is None:
            violations.append("%s: no frontmatter block" % rel)
            continue
        for field in REQUIRED:
            if not re.search(r"^%s:" % field, fm, re.M):
                violations.append("%s: missing frontmatter field '%s'" % (rel, field))
        m = re.search(r"^license:\s*(.+)$", fm, re.M)
        if m and m.group(1).strip().strip('"\'') != "MIT":
            violations.append("%s: license is not MIT: %s" % (rel, m.group(1).strip()))
        a = re.search(r"^author:\s*(.+)$", fm, re.M)
        if a and a.group(1).strip().strip('"\'') not in ALLOWED_AUTHORS:
            violations.append("%s: author field is not the neutral attribution line: %s"
                              % (rel, a.group(1).strip()))
    if scanned == 0:
        print("gate error: no skills/*/SKILL.md found")
        return 2
    if violations:
        print("FRONTMATTER VIOLATION: " + str(len(violations)))
        for v in violations:
            print("  " + v)
        return 1
    print("clean: " + str(scanned) + " skills carry name, description, version, and MIT license")
    return 0


if __name__ == "__main__":
    sys.exit(main())
