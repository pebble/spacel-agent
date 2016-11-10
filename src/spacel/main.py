#!/usr/bin/env python

import sys

from spacel.cli import cli

if __name__ == '__main__':  # pragma: no cover
    if len(sys.argv) == 1:
        sys.argv += ('services',)
    cli()
