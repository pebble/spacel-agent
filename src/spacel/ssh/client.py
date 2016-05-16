#!/usr/bin/env python

import logging
from spacel.aws import AwsMeta, ClientCache
from spacel.log import setup_logging
from spacel.ssh.db import SshDb

logger = logging.getLogger('spacel')


def main(args):
    meta = AwsMeta()
    clients = ClientCache(meta.region)

    db = SshDb(clients, meta)
    if meta.bastion:
        keys = db.bastion_keys()
    else:
        keys = db.service_keys(meta.name)

    print '\n'.join(keys)


if __name__ == '__main__':  # pragma: no cover
    import sys

    setup_logging()
    main(sys.argv)
