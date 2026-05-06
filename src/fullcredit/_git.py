from __future__ import annotations

import os
import shlex
import subprocess
import textwrap


class FullcreditSubprocessError(Exception):
    pass


class GitLog:
    def __init__(
        self,
        log_format: str,
        *,
        repo: str | None = None,
        revspec: str | None = None,
    ) -> None:
        self._format = f"{log_format}"
        self._repo = os.path.abspath(repo or ".")
        self._args = ["git", "-C", self._repo, "log", f"--format={self._format}"]
        if revspec:
            self._args.append(revspec)

    def run(self) -> str:
        process = subprocess.run(
            self._args,
            text=True,
            capture_output=True,
            check=False,
        )
        if process.returncode != 0:
            raise FullcreditSubprocessError(
                f"`{self}` did not run successfully (exit code was"
                f" {process.returncode})\n"
                + textwrap.indent(process.stderr, prefix="  ")
                + "This error originates from a subprocess."
            )
        return process.stdout

    def __str__(self) -> str:
        return shlex.join(self._args)

    def __repr__(self) -> str:
        return f"GitLog({self._format!r}, repo={self._repo!r})"
