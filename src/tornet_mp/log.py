"""Lightweight wrapper around the standard *logging* module.

The colour helpers are kept for backward-compat but forward everything
through ``logging.getLogger("tornet_mp")`` so library users can
configure handlers the usual way.

Use::

    import logging, tornet_mp.log as log

    logging.basicConfig(level=logging.INFO)
    log.log_info("Hello!")

"""

from __future__ import annotations

import logging
import sys

_logger = logging.getLogger("tornet_mp")

# ANSI colours (will be stripped by logging handlers that don't support them)
white = "\033[97m"
green = "\033[92m"
red = "\033[91m"
yellow = "\033[93m"
blue = "\033[94m"
magenta = "\033[95m"
cyan = "\033[36m"
gray = "\033[90m"
reset = "\033[0m"


def configure(level: int = logging.DEBUG) -> None:
    """Convenience helper to quickly configure root logging."""
    if not _logger.handlers:
        handler = logging.StreamHandler(stream=sys.stderr)
        handler.setFormatter(logging.Formatter("%(message)s"))
        _logger.addHandler(handler)
    _logger.setLevel(level)


def log(
    message: str, tag: str = "+", color: str = white, level: int = logging.INFO
) -> None:
    _logger.log(level, f"[{color}{tag}{reset}] {color}{message}{reset}")


def log_success(msg: str) -> None:
    log(msg, tag="+", color=green, level=logging.INFO)


def log_info(msg: str) -> None:
    log(msg, tag="~", color=blue, level=logging.INFO)


def log_notice(msg: str) -> None:
    log(msg, tag="*", color=cyan, level=logging.INFO)


def log_minor(msg: str) -> None:
    log(msg, tag="~", color=gray, level=logging.DEBUG)


def log_warn(msg: str) -> None:
    log(msg, tag="!", color=yellow, level=logging.WARNING)


def log_error(msg: str) -> None:
    log(msg, tag="!", color=red, level=logging.ERROR)


def log_change(msg: str) -> None:
    log(msg, tag="+", color=magenta, level=logging.INFO)
