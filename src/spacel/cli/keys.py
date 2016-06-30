import click
from spacel.aws import AwsMeta, ClientCache
from spacel.ssh.db import SshDb
import logging

logger = logging.getLogger('spacel')


@click.group()
def keys_cmd():  # pragma: no cover
    pass


@keys_cmd.command(
        help='Get authorized SSH keys, intended as AuthorizedKeysCommand.')
def keys():  # pragma: no cover
    get_keys()


def get_keys():
    meta = AwsMeta()
    clients = ClientCache(meta.region)

    db = SshDb(clients, meta)
    if meta.bastion:
        keys = db.bastion_keys()
    else:
        keys = db.service_keys(meta.name)

    print '\n'.join(keys)
