import sys

_SERVER = "http://bobconda.lab.idiap.ch"


def _get_target_channel(public, stable, server, group):
    """Returns the target channel for deployment

    Args:

      public: Boolean indicating if we're supposed to include only public
        channels
      stable: Boolean indicating if we're supposed to include stable channels
      server: The base address of the server containing our conda channels
      group: The group of packages (gitlab namespace) the package we're
        compiling is part of.  Values should match URL namespaces currently
        available on our internal webserver.  Currently, only "bob" or "beat"
        will work.

    Returns:

        the channel to deploy to

    """

    if public:
        prefix = "/software/" + group
        if stable:
            return server + prefix + "/conda"
        else:
            return server + prefix + "/conda/label/beta"
    else:
        prefix = "/private"
        if stable:
            return server + prefix + "/conda"
        else:
            return server + prefix + "/conda/label/beta"


def _next_build_number(channel_url, name, version, build_variant):
    """Calculates the next build number of a package given the channel.

    This function returns the next build number (integer) for a package given
    its resulting tarball base filename (can be obtained with
    :py:func:`get_output_path`).


    Args:

      channel_url: The URL where to look for packages clashes (normally a beta
        channel)
      name: The package name
      version: The package version
      build_variant: The build variant to consider

    Returns: The next build number with the current configuration.  Zero (0) is
    returned if no match is found.  Also returns the URLs of the packages it
    finds with matches on the name, version and python-version, ordered by
    (reversed) build-number.
    """

    from conda.core.index import calculate_channel_urls
    from conda.exports import fetch_index

    # get the channel index
    channel_urls = calculate_channel_urls(
        [channel_url], prepend=False, use_local=False
    )
    # print(f"Looking up:")
    # for k in channel_urls:
    #    print(f"  - {k}")
    index = fetch_index(channel_urls=channel_urls)

    # search if package with the same characteristics
    urls = {}
    build_number = 0

    for dist in index:
        if (
            dist.name == name
            and dist.version == version
            and dist.build_string.startswith(build_variant)
        ):  # match!
            url = index[dist].url
            # print(f"Found match at {url} for {name}-{version}")
            build_number = max(build_number, dist.build_number + 1)
            urls[index[dist].timestamp] = url.replace(channel_url, "")
        # else:
        #    print(f"discarded {dist.name}-{dist.version}-{dist.build_string} != {name}-{version}-{build_variant}")

    sorted_urls = [urls[k] for k in reversed(list(urls.keys()))]

    return build_number, sorted_urls


if __name__ == "__main__":

    if len(sys.argv) != 7:
        print(f"usage: {sys.argv[0]} group visibility tag name version variant")
        sys.exit(1)

    group = sys.argv[1]
    visibility = sys.argv[2]
    tag = sys.argv[3]
    name = sys.argv[4]
    version = sys.argv[5]
    variant = sys.argv[6]

    # compute entries
    public = visibility == "public"
    stable = bool(tag)

    channel = _get_target_channel(public, stable, _SERVER, group)
    bn, matches = _next_build_number(channel, name, version, variant)
    print(f"{bn}")

    if matches:
        with open("conda-package-matches.txt", "wt") as f:
            for k in matches:
                f.write(f"{channel}{k}\n")
