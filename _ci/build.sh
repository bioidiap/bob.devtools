#!/usr/bin/env bash

# datetime prefix for logging
log_datetime() {
	echo "($(date +%T.%3N))"
}

# Functions for coloring echo commands
log_info() {
  echo -e "$(log_datetime) \033[1;34m${@}\033[0m"
}


log_error() {
  echo -e "$(log_datetime) \033[1;31mError: ${@}\033[0m" >&2
}


# Checks just if the variable is defined and has non-zero length
check_defined() {
  if [ -z "${!1+abc}" ]; then
    log_error "Variable ${1} is undefined - aborting...";
    exit 1
  elif [ -z "${!1}" ]; then
    log_error "Variable ${1} is zero-length - aborting...";
    exit 1
  fi
}


# Exports a given environment variable, verbosely
export_env() {
  check_defined "${1}"
  export ${1}
  log_info "export ${1}=${!1}"
}

check_defined CONDA_ROOT
check_defined CI_PROJECT_DIR
check_defined CI_PROJECT_NAME
check_defined CI_COMMIT_TAG
check_defined PYTHON_VERSION

BOB_PACKAGE_VERSION=`cat version.txt | tr -d '\n'`;
check_defined BOB_PACKAGE_VERSION

# Makes sure we activate the base environment if available
run_cmd source ${CONDA_ROOT}/etc/profile.d/conda.sh
run_cmd conda activate base
export_env PATH

if [ -z "${CI_COMMIT_TAG}" ]; then #building beta
  channel="http://www.idiap.ch/public/conda/label/beta"
else
  channel="http://www.idiap.ch/public/conda"
fi

log_info "$ ${CONDA_ROOT}/bin/python ${CI_PROJECT_DIR}/_ci/nextbuild.py ${channel} ${CI_PROJECT_NAME} ${BOB_PACKAGE_VERSION} ${PYTHON_VERSION}"
BOB_BUILD_NUMBER=$(${CONDA_ROOT}/bin/python ${CI_PROJECT_DIR}/_ci/nextbuild.py ${channel} ${CI_PROJECT_NAME} ${BOB_PACKAGE_VERSION} ${PYTHON_VERSION})
export_env BOB_BUILD_NUMBER

# copy the recipe_append.yaml over before build
run_cmd cp ${CI_PROJECT_DIR}/bob/devtools/data/recipe_append.yaml conda/
run_cmd cp ${CI_PROJECT_DIR}/bob/devtools/data/conda_build_config.yaml conda/

run_cmd ${CONDA_ROOT}/bin/conda build "--python=${PYTHON_VERSION} --no-anaconda-upload" conda

# run git clean to clean everything that is not needed. This helps to keep the
# disk usage on CI machines to minimum.
if [ "$(uname -s)" == "Linux" ]; then _os="linux" else _os="osx"; fi
run_cmd git clean -ffdx \
    --exclude="miniconda.sh" \
    --exclude="miniconda/pkgs/*.tar.bz2" \
    --exclude="miniconda/pkgs/urls.txt" \
    --exclude="miniconda/conda-bld/${_os}-64/*.tar.bz2" \
    --exclude="_ci" \
    --exclude="dist/*.zip" \
    --exclude="sphinx"
