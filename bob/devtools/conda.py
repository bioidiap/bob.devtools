
def should_skip_build(metadata_tuples):
    """Takes the output of render_recipe as input and evaluates if this
    recipe's build should be skipped.
    """
    return all(m[0].skip() for m in metadata_tuples)
