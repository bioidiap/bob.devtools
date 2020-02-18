import click


def ref_option(**kwargs):
    """An option for getting branch name."""

    def custom_ref_option(func):

        return click.option(
            "-r",
            "--ref",
            default="master",
            show_default=True,
            help="Download path from the provided git reference (may be a branch, tag or commit hash)",
            **kwargs
        )(func)

    return custom_ref_option
