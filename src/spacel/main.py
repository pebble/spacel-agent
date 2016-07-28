#!/usr/bin/env python

from spacel.cli import cli
import sys

if __name__ == '__main__':  # pragma: no cover
    if len(sys.argv) == 1:
        sys.argv += ('services',)
    cli()
