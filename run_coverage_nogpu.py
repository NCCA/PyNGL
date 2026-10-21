#!/usr/bin/env -S uv run --script

"""Collect full-suite coverage for SonarCloud using native or software graphics.

The historical filename is retained for existing callers. Linux CI provides
Mesa and a virtual display so graphics tests can run without a physical GPU.
"""

import subprocess
import sys


def main() -> None:
    """Run the tests and stop if testing or report generation fails."""
    coverage = [sys.executable, "-m", "coverage"]
    subprocess.run(
        [*coverage, "run", "-m", "pytest", "tests", "--run-graphics", "-q"],
        check=True,
    )
    subprocess.run([*coverage, "xml"], check=True)
    subprocess.run([*coverage, "report", "-m", "--fail-under=80"], check=True)
    subprocess.run([*coverage, "html"], check=True)


if __name__ == "__main__":
    main()
