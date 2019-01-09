#!/usr/bin/env bash

source $(dirname ${0})/functions.sh

# delete the bob packages from the cache otherwise the cache keeps increasing
# over and over. See https://gitlab.idiap.ch/bob/bob.admin/issues/65
run_cmd rm -rf ${CONDA_ROOT}/pkgs/bob*.tar.bz2

# run git clean to clean everything that is not needed. This helps to keep the
# disk usage on CI machines to minimum.
run_cmd git clean -ffdx \
    --exclude="miniconda.sh" \
    --exclude="miniconda/pkgs/*.tar.bz2" \
    --exclude="miniconda/pkgs/urls.txt" \
    --exclude="miniconda/conda-bld/${OS_SLUG}/*.tar.bz2" \
    --exclude="_ci" \
    --exclude="dist/*.zip" \
    --exclude="sphinx"
