#!/usr/bin/env python3
"""Exercises the frontmatter gate: clean on the repo, red on a bad fixture."""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATE = os.path.join(ROOT, "gates", "protean-github-flow", "check-skill-frontmatter.py")


def run(tree):
    return subprocess.run([sys.executable, GATE, tree], capture_output=True,
                          text=True, timeout=120)


class TestFrontmatter(unittest.TestCase):
    def test_passes_on_repo(self):
        result = run(ROOT)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_fails_on_personal_author(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill = os.path.join(tmp, "skills", "x")
            os.makedirs(skill)
            with open(os.path.join(skill, "SKILL.md"), "w", encoding="utf-8") as fh:
                fh.write("---\nname: x\ndescription: \"d\"\nversion: 1.0.0\n"
                         "license: MIT\nauthor: a person\n---\n\nbody\n")
            result = run(tmp)
            self.assertEqual(result.returncode, 1)
            self.assertIn("not the neutral attribution line", result.stdout)

    def test_fails_on_missing_license(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill = os.path.join(tmp, "skills", "x")
            os.makedirs(skill)
            with open(os.path.join(skill, "SKILL.md"), "w", encoding="utf-8") as fh:
                fh.write("---\nname: x\ndescription: \"d\"\nversion: 1.0.0\n---\n\nbody\n")
            result = run(tmp)
            self.assertEqual(result.returncode, 1)
            self.assertIn("missing frontmatter field 'license'", result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
