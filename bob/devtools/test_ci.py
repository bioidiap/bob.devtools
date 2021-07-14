#!/usr/bin/env python
# coding=utf-8
import json

from .ci import is_private
from .constants import BOBRC_PATH


def test_is_private():

    base_url = "https://gitlab.idiap.ch"
    assert not is_private(base_url, "bob/bob.extension")
    assert is_private(base_url, "bob/private")


def test_bobrc_json_validity():

    with open(BOBRC_PATH) as f:
        json.load(f)
