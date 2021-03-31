import click

from ..log import verbosity_option
from . import bdt


@click.command(
    epilog="""
Examples:

  1. Runs an alternate to nightly builds following a list of packages in a file:

     $ bdt gitlab alt-nightlies -vv order.txt

  2. Provide a list of key value pairs of arguments to be used as variables in the CI

     $ bdt gitlab alt-nightlies -vv order.txt TEST_MARK_EXPR "not slow"
"""
)
@click.argument(
    "order",
    required=True,
    type=click.Path(file_okay=True, dir_okay=False, exists=True),
    nargs=1,
)
@click.argument(
    "variables",
    nargs=-1,
)
@verbosity_option()
@bdt.raise_on_error
def alt_nightlies(order, variables):
    """Alternative nightlies.
    This command should be run locally and not in Gitlab CI.
    It will trigger a pipeline for each package in the order file
    """
    if not variables:
        variables = []
    final_variables = []
    for i, v in enumerate(variables):
        if i % 2 == 1:
            continue
        final_variables.append({"key": v, "value": variables[i + 1]})

    import time

    from ..ci import read_packages
    from ..log import get_logger
    from ..release import get_gitlab_instance

    logger = get_logger(__name__)

    gl = get_gitlab_instance()
    packages = read_packages(order)

    for n, (package, branch) in enumerate(packages):

        # trigger a pipeline for package and branch
        project = gl.projects.get(package)
        logger.info(
            f"Creating a pipeline for {package} branch {branch} with variables {final_variables}"
        )
        pipeline = project.pipelines.create(
            {"ref": branch, "variables": final_variables}
        )

        # wait for it to finish
        while pipeline.status in ("pending", "running"):
            time.sleep(3)
            pipeline.refresh()
            continue

        if pipeline.status == "success":
            continue

        raise RuntimeError(f"Pipeline {pipeline.web_url} {pipeline.status}")
