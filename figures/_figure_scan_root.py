"""Scan-root resolution for the figure sensors.

The sensors were extracted from the MAGE book build, where every one of them
hardcoded ``book/assets`` as its scan root. In the portfolio each site owns its
own ``figures/`` directory, so the root has to be a parameter.

Resolution order, first hit wins:

1. ``$FIGURE_SCAN_ROOT``      -- set by ``check_figures.py`` before it imports
                                 the sensors; also usable directly.
2. ``./figures``              -- the convention, when run from a site root.
3. the current directory      -- when run from inside ``figures/`` itself.

The sensors resolve this at import time, before their own ``argparse`` runs,
which is why an environment variable rather than a flag carries it. Passing
explicit ``.svg`` paths on a sensor's command line still overrides the root
entirely -- that path is untouched.
"""

from __future__ import annotations

import os
import pathlib

ENV_VAR = "FIGURE_SCAN_ROOT"


def scan_root() -> pathlib.Path:
    """Directory the sensors glob ``*.svg`` from."""
    explicit = os.environ.get(ENV_VAR)
    if explicit:
        return pathlib.Path(explicit).expanduser().resolve()

    cwd = pathlib.Path.cwd()
    conventional = cwd / "figures"
    if conventional.is_dir():
        return conventional.resolve()

    return cwd.resolve()
