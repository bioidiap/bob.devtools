import click

from click_plugins import with_plugins
from pkg_resources import iter_entry_points


@click.command(epilog="See bdt dev --help")
@click.argument(
    "folders",
    nargs=-1,
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
def install(folders):
    """runs pip install -vvv --no-build-isolation --no-dependencies --editable <folder>"""
    import os
    import subprocess

    for folder in folders:
        if not os.path.exists(os.path.join(folder, "setup.py")):
            raise click.ClickException(
                "Folder does not contain a setup.py: %s" % folder
            )

        # call pip
        subprocess.check_call(
            [
                "pip",
                "install",
                "-vvv",
                "--no-build-isolation",
                "--no-dependencies",
                "--editable",
                folder,
            ]
        )


@click.command(epilog="See bdt dev --help")
@click.argument("names", nargs=-1)
@click.option("--use-https/--use-ssh", is_flag=True, default=False)
@click.option(
    "-s", "--subfolder", default="", help="subfolder to checkout into"
)
@click.pass_context
def checkout(ctx, names, use_https, subfolder):
    """git clones a Bob package."""
    import os
    import subprocess

    # create the subfolder directory
    if subfolder:
        os.path.makedirs(subfolder, exist_ok=True)

    for name in names:

        # call git
        # skip if the directory already exists
        dest = name
        if subfolder:
            dest = os.path.join(subfolder, name)

        if not os.path.isdir(dest):

            url = f"git@gitlab.idiap.ch:bob/{name}.git"
            if use_https:
                url = f"https://gitlab.idiap.ch/bob/{name}.git"

            subprocess.check_call(["git", "clone", url, dest])


@with_plugins(iter_entry_points("bdt.dev.cli"))
@click.group(
    epilog="""Examples:

\b
# develop an existing project
bdt dev checkout bob.bio.face
cd bob.bio.face
bdt dev create --python 3.9 bobbioface
bdt dev install .

\b
# later on, checkout and develop more packages
bdt dev checkout --subfolder src bob.bio.base
bdt dev install src/bob.bio.base

\b
# develop a new project
bdt dev new -vv bob/bob.newpackage "John Doe" "joe@example.com"
# edit the conda/meta.yaml and requirements.txt files to add your dependencies
bdt dev create --python 3.9 bobnewpackage
bdt install ."""
)
def dev():
    """Development scripts"""
    pass
