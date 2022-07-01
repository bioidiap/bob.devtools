import click

from click_plugins import with_plugins
from pkg_resources import iter_entry_points


@click.command(epilog="See bdt dev --help for examples of this command.")
@click.option(
    "-n",
    "--env-name",
    help="Name of the conda environment to use",
    required=True,
)
@click.argument(
    "folders",
    nargs=-1,
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
def install(env_name, folders):
    """runs:

    pip install -vvv --no-build-isolation --no-dependencies --editable <folder>

    inside the specified conda environment"""
    import subprocess

    for folder in folders:

        # call pip
        cmd = [
            "conda",
            "run",
            "-n",
            env_name,
            "pip",
            "install",
            "-vvv",
            "--no-build-isolation",
            "--no-dependencies",
            "--editable",
            folder,
        ]
        cmd = " ".join(cmd)
        subprocess.check_call(
            cmd,
            shell=True,
        )
        click.echo(f"Installed package using the command: {cmd}")


@click.command(epilog="See bdt dev --help for examples of this command.")
@click.argument("names", nargs=-1)
@click.option("--use-https/--use-ssh", is_flag=True, default=False)
@click.option(
    "-s", "--subfolder", default="", help="subfolder to checkout into"
)
@click.pass_context
def checkout(ctx, names, use_https, subfolder):
    """git clones a Bob package and installs the pre-commit hook if required."""
    import os
    import subprocess

    # create the subfolder directory
    if subfolder:
        os.makedirs(subfolder, exist_ok=True)

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

            # call pre-commit if its configuration exists
            if os.path.isfile(os.path.join(dest, ".pre-commit-config.yaml")):
                click.echo(
                    "Installing pre-commit hooks. Make sure you have pre-commit installed."
                )
                try:
                    subprocess.check_call(["pre-commit", "install"], cwd=dest)
                except subprocess.CalledProcessError:
                    click.echo(
                        "pre-commit git hook installation failed. "
                        "Please make sure you have pre-commit installed "
                        "and its binary is in the PATH."
                    )
                    raise


# the group command must be at the end of this file for plugins to work.
@with_plugins(iter_entry_points("bdt.dev.cli"))
@click.group(
    epilog="""Examples:

\b
# develop an existing project
bdt dev checkout bob.bio.face
cd bob.bio.face
bdt dev create --python 3.9 bobbioface
bdt dev install -n bobbioface .

\b
# later on, checkout and develop more packages
bdt dev checkout --subfolder src bob.bio.base
bdt dev install -n bobbioface src/bob.bio.base

\b
# develop a new project
bdt dev new -vv bob/bob.newpackage "John Doe" "joe@example.com"
# edit the conda/meta.yaml and requirements.txt files to add your dependencies
bdt dev create --python 3.9 bobnewpackage
bdt install -n bobnewpackage .

\b
# create an environment with all external bob dependencies
bdt dev dependencies --python 3.9 my_env
"""
)
def dev():
    """Development scripts"""
    pass
