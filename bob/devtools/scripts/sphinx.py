import click


@click.group()
def sphinx():
    pass


@sphinx.command()
@click.argument(
    "sphix_configurations",
    type=click.Path(exists=True, dir_okay=False),
    required=False,
    nargs=-1,
)
def migrate_autodoc_flags(sphix_configurations):
    if not sphix_configurations:
        sphix_configurations = ["doc/conf.py"]
    for sphinx_config in sphix_configurations:
        with open(sphinx_config) as f:
            config = f.read()

        config = config.replace(
            """autodoc_default_flags = [
  'members',
  'undoc-members',
  'show-inheritance',
  ]""",
            """autodoc_default_options = {
  "members": True,
  "undoc-members": True,
  "show-inheritance": True,
}""",
        )

        # another variant
        config = config.replace(
            """autodoc_default_flags = [
    "members",
    "undoc-members",
    "show-inheritance",
]""",
            """autodoc_default_options = {
  "members": True,
  "undoc-members": True,
  "show-inheritance": True,
}""",
        )

        # another variant
        config = config.replace(
            """autodoc_default_flags = [
    'members',
    'undoc-members',
    'show-inheritance',
]""",
            """autodoc_default_options = {
  "members": True,
  "undoc-members": True,
  "show-inheritance": True,
}""",
        )

        # another variant
        config = config.replace(
            """autodoc_default_flags = [
  'members',
  'undoc-members',
  'inherited-members',
  'show-inheritance',
  ]""",
            """autodoc_default_options = {
  "members": True,
  "undoc-members": True,
  "inherited-members": True,
  "show-inheritance": True,
}""",
        )

        # another variant
        config = config.replace(
            """autodoc_default_flags = ["members", "undoc-members", "show-inheritance"]""",
            """autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}""",
        )

        config = config.replace(
            """# We want to remove all private (i.e. _. or __.__) members
# that are not in the list of accepted functions
accepted_private_functions = ['__array__']

def member_function_test(app, what, name, obj, skip, options):
  # test if we have a private function
  if len(name) > 1 and name[0] == '_':
    # test if this private function should be allowed
    if name not in accepted_private_functions:
      # omit privat functions that are not in the list of accepted private functions
      return skip
    else:
      # test if the method is documented
      if not hasattr(obj, '__doc__') or not obj.__doc__:
        return skip
  return False

def setup(app):
  app.connect('autodoc-skip-member', member_function_test)
""",
            "",
        )

        # another variant
        config = config.replace(
            """# We want to remove all private (i.e. _. or __.__) members
# that are not in the list of accepted functions
accepted_private_functions = ['__array__']


def member_function_test(app, what, name, obj, skip, options):
    # test if we have a private function
    if len(name) > 1 and name[0] == '_':
        # test if this private function should be allowed
        if name not in accepted_private_functions:
            # omit privat functions that are not in the list of accepted private functions
            return skip
        else:
            # test if the method is documented
            if not hasattr(obj, '__doc__') or not obj.__doc__:
                return skip
    return False


def setup(app):
    app.connect('autodoc-skip-member', member_function_test)
""",
            "",
        )

        # another variant
        config = config.replace(
            """# We want to remove all private (i.e. _. or __.__) members
# that are not in the list of accepted functions
accepted_private_functions = ["__array__"]


def member_function_test(app, what, name, obj, skip, options):
    # test if we have a private function
    if len(name) > 1 and name[0] == "_":
        # test if this private function should be allowed
        if name not in accepted_private_functions:
            # omit privat functions that are not in the list of accepted private functions
            return skip
        else:
            # test if the method is documented
            if not hasattr(obj, "__doc__") or not obj.__doc__:
                return skip
    return False


def setup(app):
    app.connect("autodoc-skip-member", member_function_test)
""",
            "",
        )

        # another variant
        config = config.replace(
            """
# We want to remove all private (i.e. _. or __.__) members
# that are not in the list of accepted functions
accepted_private_functions = ["__array__"]


def member_function_test(app, what, name, obj, skip, options):
    # test if we have a private function
    if len(name) > 1 and name[0] == "_":
        # test if this private function should be allowed
        if name not in accepted_private_functions:
            # omit private functions that are not in the list of accepted private
            # functions
            return skip
        else:
            # test if the method is documented
            if not hasattr(obj, "__doc__") or not obj.__doc__:
                return skip
    return False


def setup(app):
    app.connect("autodoc-skip-member", member_function_test)
""",
            "",
        )

        with open(sphinx_config, "w") as f:
            f.write(config)
