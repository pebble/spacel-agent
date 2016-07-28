import click
from .keys import keys_cmd
from .services import services_cmd

commands = (keys_cmd, services_cmd)
cli = click.CommandCollection(sources=commands)
