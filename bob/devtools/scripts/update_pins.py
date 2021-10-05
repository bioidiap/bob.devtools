"""Updates the pin versions inside bob/devtools/data/conda_build_config.yaml"""

import click


@click.command()
@click.option("--python", required=True, help="Python version to pin, e.g. 3.8")
def update_pins(python):
    from subprocess import check_output

    from bob.devtools.build import load_packages_from_conda_build_config

    conda_config_path = "bob/devtools/data/conda_build_config.yaml"

    packages, package_names_map = load_packages_from_conda_build_config(
        conda_config_path, {"channels": []}
    )
    reversed_package_names_map = {v: k for k, v in package_names_map.items()}

    # ask mamba to create an environment with the packages
    env_text = check_output(
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
    ).decode("utf-8")
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
        f"{reversed_package_names_map.get(name, name)}:\n  - {version}"
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
