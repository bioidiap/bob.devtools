"""This is the main entry to bob_tools's scripts.
"""
import pkg_resources
import click
from click_plugins import with_plugins


@with_plugins(pkg_resources.iter_entry_points('bob_tools.cli'))
@click.group(context_settings=dict(help_option_names=['-?', '-h', '--help']))
def main():
    """The main command line interface for bob tools. Look below for available
    commands."""
    pass
