import click
from .keys import keys_cmd

commands = keys_cmd
cli = click.CommandCollection(sources=commands)
