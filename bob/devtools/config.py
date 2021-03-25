#!/usr/bin/env python
# coding=utf-8

"""Reads and treats configuration files"""


import configparser
import os


def read_config():
    """Reads and resolves configuration files, returns a dictionary with read
    values"""

    data = configparser.ConfigParser()
    cfg = os.path.expanduser("~/.bdtrc")
    if os.path.exists(cfg):
        data.read(cfg)
    return data
