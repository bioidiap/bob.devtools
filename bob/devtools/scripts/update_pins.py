"""Updates the pin versions inside bob/devtools/data/conda_build_config.yaml"""

import click


@click.command(
    epilog="""Example:

python bob/devtools/scripts/update_pins.py --python 3.8

Force specific version of packages:

python bob/devtools/scripts/update_pins.py --python 3.8 opencv=4.5.1 pytorch=1.9
"""
)
@click.argument("manual_pins", nargs=-1)
@click.option("--python", required=True, help="Python version to pin, e.g. 3.8")
def update_pins(manual_pins, python):
    import subprocess

    from bob.devtools.build import load_packages_from_conda_build_config

    conda_config_path = "bob/devtools/data/conda_build_config.yaml"

    packages, package_names_map = load_packages_from_conda_build_config(
        conda_config_path, {"channels": []}
    )
    reversed_package_names_map = {v: k for k, v in package_names_map.items()}

    # ask mamba to create an environment with the packages
    try:
        output = subprocess.run(
            [
                "mamba",
                "create",
                "--dry-run",
                "--override-channels",
                "-c",
                "conda-forge",
                "-n",
                "temp_env",
                f"python={python}",
            ]
            + packages
            + list(manual_pins),
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(e.output.decode())
        raise e

    env_text = output.stdout.decode("utf-8")
    print(env_text)

    resolved_packages = []
    for line in env_text.split("\n"):
        line = line.strip()
        if line.startswith("+ "):
            line = line.split()
            name, version = line[1], line[2]
            resolved_packages.append((name, version))

    # write the new pinning
    with open(conda_config_path, "r") as f:
        content = f.read()

    START = """
# AUTOMATIC PARSING START
# DO NOT MODIFY THIS COMMENT

# list all packages with dashes or dots in their names, here:"""
    idx1 = content.find(START)
    idx2 = content.find("# AUTOMATIC PARSING END")
    pins = "\n".join(
        f'{reversed_package_names_map.get(name, name)}:\n  - "{version}"'
        for name, version in resolved_packages
        if name in packages
    )
    package_names_map_str = "\n".join(
        f"  {k}: {v}" for k, v in package_names_map.items()
    )

    new_content = f"""{START}
package_names_map:
{package_names_map_str}


{pins}

"""

    content = content[:idx1] + new_content + content[idx2:]
    with open(conda_config_path, "w") as f:
        f.write(content)


if __name__ == "__main__":
    update_pins()
