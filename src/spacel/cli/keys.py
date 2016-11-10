import logging

import click

from spacel.aws import AwsMeta, ClientCache
from spacel.log import setup_logging
from spacel.ssh.db import SshDb

logger = logging.getLogger('spacel')


@click.group()
def keys_cmd():  # pragma: no cover
    pass


@keys_cmd.command(help='Get authorized SSH keys.')
def keys():  # pragma: no cover
    get_keys()


def get_keys():
    setup_logging(logging.WARN)

    meta = AwsMeta()
    clients = ClientCache(meta.region)

    db = SshDb(clients, meta)
    if meta.bastion:
        keys = db.bastion_keys()
    else:
        keys = db.service_keys(meta.name)

    print '\n'.join(keys)
