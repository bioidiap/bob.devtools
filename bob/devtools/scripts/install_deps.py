"""Create an environment with all external dependencies listed in bob/devtools/data/conda_build_config.yaml"""
import click


@click.command(
    epilog="""Example:
  1. Creates an environment called `myenv' containing all external bob dependencies:

python bob/devtools/scripts/install_deps.py  myenv

2. The version of python to solve with can be provided as option:

python bob/devtools/scripts/install_deps.py  myenv --python=3.8

"""
)
@click.argument("env_name", nargs=1)
@click.option("--python", required=True, help="Python version to pin, e.g. 3.8")
def install_deps(env_name, python):
    import subprocess

    from bob.devtools.build import load_packages_from_conda_build_config

    conda_config_path = "bob/devtools/data/conda_build_config.yaml"

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
            + packages,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(e.output.decode())
        raise e


if __name__ == "__main__":
    install_deps()
