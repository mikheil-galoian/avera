"""pytest configuration for AVERA test suite.

Redirects absolute Mac filesystem paths to the sandbox mount point so that
tests using hard-coded /Users/mac/Desktop/AVERA/... paths work correctly
when executed inside the Linux sandbox, where the workspace is mounted at
/sessions/gallant-cool-hamilton/mnt/AVERA/.
"""

from __future__ import annotations

import os
import pathlib

# ---------------------------------------------------------------------------
# Path redirection: Mac absolute paths → sandbox mount
# ---------------------------------------------------------------------------

_MAC_PREFIX = "/Users/mac/Desktop/AVERA"
_SANDBOX_PREFIX = "/sessions/gallant-cool-hamilton/mnt/AVERA"

_orig_open = pathlib.Path.open


def _patched_open(
    self: pathlib.Path,
    mode: str = "r",
    buffering: int = -1,
    encoding: str | None = None,
    errors: str | None = None,
    newline: str | None = None,
) -> object:
    path_str = str(self)
    if path_str.startswith(_MAC_PREFIX) and not os.path.exists(path_str):
        redirected = pathlib.Path(
            _SANDBOX_PREFIX + path_str[len(_MAC_PREFIX):]
        )
        return _orig_open(redirected, mode, buffering, encoding, errors, newline)
    return _orig_open(self, mode, buffering, encoding, errors, newline)


# Only activate the redirect when running inside the sandbox
if os.path.isdir(_SANDBOX_PREFIX) and not os.path.isdir(_MAC_PREFIX):
    pathlib.Path.open = _patched_open  # type: ignore[method-assign]
