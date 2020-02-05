import click
import logging

from restore import restore_command
from backup import backup_command

DEFAULT_LOG_FMT = '%(asctime)-15s %(name)s:%(lineno)s - %(funcName)s() %(levelname)s - %(message)s'
logging.basicConfig(format=DEFAULT_LOG_FMT, level=logging.INFO)


@click.group()
def cli():
    pass


cli.add_command(restore_command, name='restore')
cli.add_command(backup_command, name='backup')

if __name__ == '__main__':
    cli(auto_envvar_prefix='DR')
