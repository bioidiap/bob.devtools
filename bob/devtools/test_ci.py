#!/usr/bin/env python
# coding=utf-8

from .ci import is_private


def test_is_private():

    base_url = "https://gitlab.idiap.ch"
    assert not is_private(base_url, "bob/bob.extension")
    assert is_private(base_url, "bob/private")
