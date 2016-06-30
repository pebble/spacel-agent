#!/usr/bin/env python

from spacel.log import setup_logging
from spacel.cli import cli

if __name__ == '__main__':  # pragma: no cover
    import logging

    setup_logging(logging.WARN)
    cli()
