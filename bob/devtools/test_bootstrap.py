#!/usr/bin/env python

from .bootstrap import get_channels


def test_get_channels():
    server, group = "idiap.ch", "bob"

    # test when building public beta packages
    public, stable = True, False
    channels, upload_channel = get_channels(
        public=public,
        stable=stable,
        server=server,
        intranet=not public,
        group=group,
    )
    assert channels == [f"{server}/software/{group}/conda/label/beta"]
    assert upload_channel == channels[0]

    # test with add_dependent_channels
    channels, upload_channel = get_channels(
        public=public,
        stable=stable,
        server=server,
        intranet=not public,
        group=group,
        add_dependent_channels=True,
    )
    assert channels == [
        f"{server}/software/{group}/conda/label/beta",
        "conda-forge",
    ]
    assert upload_channel == channels[0]

    # test when building public stable packages
    public, stable = True, True
    channels, upload_channel = get_channels(
        public=public,
        stable=stable,
        server=server,
        intranet=not public,
        group=group,
    )
    assert channels == [f"{server}/software/{group}/conda"]
    assert upload_channel == channels[0]

    # test when building private beta packages
    public, stable = False, False
    channels, upload_channel = get_channels(
        public=public,
        stable=stable,
        server=server,
        intranet=not public,
        group=group,
    )
    assert channels == [
        f"{server}/software/{group}/conda/label/beta",
        f"{server}/private/conda/label/beta",
    ]
    assert upload_channel == channels[1]

    # test when building private stable packages
    public, stable = False, True
    channels, upload_channel = get_channels(
        public=public,
        stable=stable,
        server=server,
        intranet=not public,
        group=group,
    )
    assert channels == [
        f"{server}/software/{group}/conda",
        f"{server}/private/conda",
    ]
    assert upload_channel == channels[1]
