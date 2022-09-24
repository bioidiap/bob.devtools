import sys

_BASE_CONDARC = """\
add_pip_as_python_dependency: false #!final
always_yes: true #!final
anaconda_upload: false #!final
channel_priority: strict #!final
conda_build: #!final
  pkg_format: '2'
default_channels: #!final
  - http://bobconda.lab.idiap.ch:8000/pkgs/main
channel_alias: http://bobconda.lab.idiap.ch:9000 #!final
quiet: true #!final
remote_connect_timeout_secs: 120.0 #!final
remote_max_retries: 50 #!final
remote_read_timeout_secs: 180.0 #!final
show_channel_urls: true #!final
ssl_verify: false #!final
channels:
"""

_SERVER = "http://bobconda.lab.idiap.ch"


def _get_channels(public, stable, server, intranet, group):
    """Returns the relevant conda channels to consider if building project.

    The subset of channels to be returned depends on the visibility and
    stability of the package being built.  Here are the rules:

    * public and stable: returns the public stable channel
    * public and not stable: returns the public beta channel
    * not public and stable: returns both public and private stable channels
    * not public and not stable: returns both public and private beta channels

    Public channels have priority over private channles, if turned.

    Args:

      public: Boolean indicating if we're supposed to include only public
        channels
      stable: Boolean indicating if we're supposed to include stable channels
      server: The base address of the server containing our conda channels
      intranet: Boolean indicating if we should add "private"/"public" prefixes
        on the conda paths
      group: The group of packages (gitlab namespace) the package we're
        compiling is part of.  Values should match URL namespaces currently
        available on our internal webserver.  Currently, only "bob" or "beat"
        will work.


    Returns: a list of channels that need to be considered.
    """

    if (not public) and (not intranet):
        raise RuntimeError(
            "You cannot request for private channels and set"
            " intranet=False (server=%s) - these are conflicting options"
            % server
        )

    channels = []
    channels_dict = {}

    # do not use '/public' urls for public channels
    prefix = "/software/" + group
    if stable:
        channels += [server + prefix + "/conda"]
        channels_dict["public/stable"] = channels[-1]
    else:
        channels += [server + prefix + "/conda/label/beta"]  # allowed betas
        channels_dict["public/beta"] = channels[-1]

    if not public:
        prefix = "/private"
        if stable:  # allowed private channels
            channels += [server + prefix + "/conda"]
            channels_dict["private/stable"] = channels[-1]
        else:
            channels += [server + prefix + "/conda/label/beta"]  # allowed betas
            channels_dict["private/beta"] = channels[-1]

    channels += ["conda-forge"]

    return channels


if __name__ == "__main__":

    if len(sys.argv) != 5:
        print(f"usage: {sys.argv[0]} group visibility tag condarc")
        sys.exit(1)

    group = sys.argv[1]
    visibility = sys.argv[2]
    tag = sys.argv[3]
    condarc = sys.argv[4]

    # compute entries
    public = visibility == "public"
    stable = bool(tag)

    channels = _get_channels(
        public=public, stable=stable, server=_SERVER, intranet=True, group=group
    )

    print(f"{condarc}: [public: {public}, stable: {stable}, group: {group}]")
    with open(condarc, "wt") as f:
        f.write(_BASE_CONDARC)
        for k in channels:
            print(f"Adding channel: {k}")
            f.write(f"  - {k}\n")
