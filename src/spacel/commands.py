#!/usr/bin/env python

from .log import setup_logging
from .cli import cli

if __name__ == '__main__':  # pragma: no cover
    import logging

    setup_logging(logging.WARN)
    cli()
