"""Create an environment with all external dependencies listed in bob/devtools/data/conda_build_config.yaml"""
import click


@click.command(
    epilog="""Example:

    Creates an environment called `myenv' based on Python 3.8 and containing all external bob dependencies:


    bdt dev dependencies --python 3.8 myenv
"""
)
@click.argument("env_name", nargs=1)
@click.option("--python", required=True, help="Python version to pin, e.g. 3.8")
def dependencies(env_name, python):
    """Creates an environment with all external bob dependencies."""
    import subprocess

    import pkg_resources

    from bob.devtools.build import load_packages_from_conda_build_config

    conda_config_path = pkg_resources.resource_filename(
        "bob.devtools", "data/conda_build_config.yaml"
    )

    packages, package_names_map = load_packages_from_conda_build_config(
        conda_config_path, {"channels": []}, with_pins=True
    )

    # ask mamba to create an environment with the packages
    try:
        _ = subprocess.run(
            [
                "mamba",
                "create",
                "--override-channels",
                "-c",
                "conda-forge",
                "-n",
                env_name,
                f"python={python}",
            ]
            + packages
            + [
                "compilers"
            ],  # Install conda-forge compilers for compiled pacakges
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(e.output.decode())
        raise e


if __name__ == "__main__":
    dependencies()
