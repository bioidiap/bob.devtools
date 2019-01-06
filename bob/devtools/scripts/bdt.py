#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Main entry point for bdt
"""

import pkg_resources

import click
from click_plugins import with_plugins

import logging
logger = logging.getLogger('bdt')


def set_verbosity_level(logger, level):
    """Sets the log level for the given logger.

    Parameters
    ----------
    logger : :py:class:`logging.Logger` or str
        The logger to generate logs for, or the name  of the module to generate
        logs for.
    level : int
        Possible log levels are: 0: Error; 1: Warning; 2: Info; 3: Debug.
    Raises
    ------
    ValueError
        If the level is not in range(0, 4).
    """
    if level not in range(0, 4):
        raise ValueError(
            "The verbosity level %d does not exist. Please reduce the number "
            "of '--verbose' parameters in your command line" % level
        )
    # set up the verbosity level of the logging system
    log_level = {
        0: logging.ERROR,
        1: logging.WARNING,
        2: logging.INFO,
        3: logging.DEBUG
    }[level]

    # set this log level to the logger with the specified name
    if isinstance(logger, str):
        logger = logging.getLogger(logger)
    logger.setLevel(log_level)


def verbosity_option(**kwargs):
    """Adds a -v/--verbose option to a click command.

    Parameters
    ----------
    **kwargs
        All kwargs are passed to click.option.

    Returns
    -------
    callable
        A decorator to be used for adding this option.
    """
    def custom_verbosity_option(f):
        def callback(ctx, param, value):
            ctx.meta['verbosity'] = value
            set_verbosity_level(logger, value)
            logger.debug("`bdt' logging level set to %d", value)
            return value
        return click.option(
            '-v', '--verbose', count=True,
            expose_value=False, default=2,
            help="Increase the verbosity level from 0 (only error messages) "
            "to 1 (warnings), 2 (info messages), 3 (debug information) by "
            "adding the --verbose option as often as desired "
            "(e.g. '-vvv' for debug).",
            callback=callback, **kwargs)(f)
    return custom_verbosity_option


class AliasedGroup(click.Group):
  ''' Class that handles prefix aliasing for commands '''
  def get_command(self, ctx, cmd_name):
    rv = click.Group.get_command(self, ctx, cmd_name)
    if rv is not None:
      return rv
    matches = [x for x in self.list_commands(ctx)
               if x.startswith(cmd_name)]
    if not matches:
      return None
    elif len(matches) == 1:
      return click.Group.get_command(self, ctx, matches[0])
    ctx.fail('Too many matches: %s' % ', '.join(sorted(matches)))


def raise_on_error(view_func):
    """Raise a click exception if returned value is not zero.

    Click exits successfully if anything is returned, in order to exit properly
    when something went wrong an exception must be raised.
    """

    from functools import wraps

    def _decorator(*args, **kwargs):
        value = view_func(*args, **kwargs)
        if value not in [None, 0]:
            exception = click.ClickException("Error occured")
            exception.exit_code = value
            raise exception
        return value
    return wraps(view_func)(_decorator)


@with_plugins(pkg_resources.iter_entry_points('bdt.cli'))
@click.group(cls=AliasedGroup,
             context_settings=dict(help_option_names=['-?', '-h', '--help']))
@verbosity_option()
def main():
    """Bob Development Tools - see available commands below"""
