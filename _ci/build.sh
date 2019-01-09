#!/usr/bin/env bash

source $(dirname ${0})/functions.sh

# Makes sure we activate the base environment if available
run_cmd source ${CONDA_ROOT}/etc/profile.d/conda.sh
run_cmd conda activate base
export_env PATH

set_conda_channels ${CI_COMMIT_TAG}
log_info "$ ${CONDA_ROOT}/bin/python ${SCRIPTS_DIR}/nextbuild.py ${DOCSERVER}/${CONDA_CHANNELS[0]} ${CI_PROJECT_NAME} ${BOB_PACKAGE_VERSION} ${PYTHON_VERSION}"
BOB_BUILD_NUMBER=$(${CONDA_ROOT}/bin/python ${SCRIPTS_DIR}/nextbuild.py ${DOCSERVER}/${CONDA_CHANNELS[0]} ${CI_PROJECT_NAME} ${BOB_PACKAGE_VERSION} ${PYTHON_VERSION})
export_env BOB_BUILD_NUMBER

# copy the recipe_append.yaml over before build
run_cmd cp ${CI_PROJECT_DIR}/bob/devtools/data/recipe_append.yaml conda/
run_cmd cp ${CI_PROJECT_DIR}/bob/devtools/data/conda_build_config.yaml conda/

BLDOPT="--python=${PYTHON_VERSION} --no-anaconda-upload"

run_cmd ${CONDA_ROOT}/bin/conda build ${BLDOPT} conda
