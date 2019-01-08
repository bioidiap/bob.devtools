#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Sets-up logging, centrally for Bob.
"""

import sys
import logging

# get the default root logger of Bob
_logger = logging.getLogger('bob')

# by default, warning and error messages should be written to sys.stderr
_warn_err = logging.StreamHandler(sys.stderr)
_warn_err.setLevel(logging.WARNING)
_logger.addHandler(_warn_err)

# debug and info messages are written to sys.stdout

class _InfoFilter:
  def filter(self, record):
    return record.levelno <= logging.INFO


_debug_info = logging.StreamHandler(sys.stdout)
_debug_info.setLevel(logging.DEBUG)
_debug_info.addFilter(_InfoFilter())
_logger.addHandler(_debug_info)


# helper functions to instantiate and set-up logging
def setup(logger_name,
    format="%(levelname)s:%(name)s@%(asctime)s: %(message)s"):
  """This function returns a logger object that is set up to perform logging
  using Bob loggers.

  Parameters
  ----------
  logger_name : str
      The name of the module to generate logs for
  format : :obj:`str`, optional
      The format of the logs, see :py:class:`logging.LogRecord` for more
      details. By default, the log contains the logger name, the log time, the
      log level and the massage.

  Returns
  -------
  logger : :py:class:`logging.Logger`
      The logger configured for logging. The same logger can be retrieved using
      the :py:func:`logging.getLogger` function.
  """
  # generate new logger object
  logger = logging.getLogger(logger_name)

  # add log the handlers if not yet done
  if not logger_name.startswith("bob") and not logger.handlers:
    logger.addHandler(_warn_err)
    logger.addHandler(_debug_info)

  # this formats the logger to print the desired information
  formatter = logging.Formatter(format)
  # we have to set the formatter to all handlers registered in the current
  # logger
  for handler in logger.handlers:
    handler.setFormatter(formatter)

  # set the same formatter for bob loggers
  for handler in _logger.handlers:
    handler.setFormatter(formatter)

  return logger


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
        "The verbosity level %d does not exist. Please reduce the number of "
        "'--verbose' parameters in your command line" % level)
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
  # set the same log level for the bob logger
  _logger.setLevel(log_level)


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
    global _logger
    import click

    def custom_verbosity_option(f):
        def callback(ctx, param, value):
            ctx.meta['verbosity'] = value
            set_verbosity_level(_logger, value)
            _logger.debug("`bob' logging level set to %d", value)
            return value
        return click.option(
            '-v', '--verbose', count=True,
            expose_value=False, default=0,
            help="Increase the verbosity level from 0 (only error messages) "
            "to 1 (warnings), 2 (info messages), 3 (debug information) by "
            "adding the --verbose option as often as desired "
            "(e.g. '-vvv' for debug).",
            callback=callback, **kwargs)(f)
    return custom_verbosity_option
