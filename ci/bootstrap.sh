#!/usr/bin/env bash

# Bootstraps a new conda installation and prepares base environment
# if "self" is passed as parameter, then self installs an already built
# version of bob.devtools available on your conda-bld directory.

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

# Function for running command and echoing results
run_cmd() {
  log_info "$ ${@}"
  ${@}
  local status=$?
  if [ ${status} != 0 ]; then
    log_error "Command Failed \"${@}\""
    exit ${status}
  fi
}

# merges conda cache folders
# $1: Path to the main cache to keep. The directory must exist.
# $2: Path to the extra cache to be merged into main cache
merge_conda_cache() {
  if [ -e ${1} ]; then
    _cached_urlstxt="${2}/urls.txt"
    _urlstxt="${1}/urls.txt"
    if [ -e ${2} ]; then
      log_info "Merging urls.txt and packages with cached files..."
      mv ${2}/*.tar.bz2 ${1}/
      cat ${_urlstxt} ${_cached_urlstxt} | sort | uniq > ${_urlstxt}
    fi
  fi
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
  log_info "${1}=${!1}"
}

# installs a miniconda installation.
# $1: Path to where to install miniconda.
install_miniconda() {
  log_info "Installing miniconda in ${1} ..."

  # checks if miniconda.sh exists
  if [ ! -e miniconda.sh ]; then
    log_info "Downloading latest miniconda3 installer..."
    # downloads the latest conda installation script
    if [ "$(uname -s)" == "Linux" ]; then
      _os="Linux"
    else
      _os="MacOSX"
    fi
    obj=https://repo.continuum.io/miniconda/Miniconda3-latest-${_os}-x86_64.sh
    run_cmd curl --silent --output miniconda.sh ${obj}
  else
    log_info "Re-using cached miniconda3 installer..."
    ls -l miniconda.sh
  fi

  # move cache to a different folder if it exists
  if [ -e ${1} ]; then
    run_cmd mv ${1} ${1}.cached
  fi

  # install miniconda
  run_cmd bash miniconda.sh -b -p ${1}

  # Put back cache and merge urls.txt
  merge_conda_cache ${1}/pkgs ${1}.cached/pkgs
  # remove the backup cache folder
  rm -rf ${1}.cached

  # List currently available packages on cache
  # run_cmd ls -l ${1}/pkgs/
  # run_cmd cat ${1}/pkgs/urls.txt

  hash -r
}


check_defined CONDA_ROOT
check_defined CI_PROJECT_DIR

export CONDARC=${CONDA_ROOT}/condarc
check_defined CONDARC

# checks if a conda installation exists. Otherwise, installs one
if [ ! -e ${CONDA_ROOT}/bin/conda ]; then
  install_miniconda ${CONDA_ROOT}
fi

run_cmd mkdir -p ${CONDA_ROOT}/pkgs
run_cmd touch ${CONDA_ROOT}/pkgs/urls
run_cmd touch ${CONDA_ROOT}/pkgs/urls.txt

run_cmd cp -fv ${CI_PROJECT_DIR}/bob/devtools/data/base-condarc ${CONDARC}
echo "channels:" >> ${CONDARC}
echo "  - http://www.idiap.ch/public/conda" >> ${CONDARC}
echo "  - defaults" >> ${CONDARC}

# displays contents of our configuration
echo "Contents of \`${CONDARC}':"
cat ${CONDARC}

# updates conda installation, installs just built bob.devtools
if [ "${1}" == "self" ]; then
  run_cmd ${CONDA_ROOT}/bin/conda create -n bdt ${CONDA_ROOT}/conda-bld/${OS_SLUG}/bob.devtools-*.tar.bz2
else
  run_cmd ${CONDA_ROOT}/bin/conda install -n base python conda=4 conda-build=3
fi

# cleans up
run_cmd ${CONDA_ROOT}/bin/conda clean --lock

# print conda information for debugging purposes
run_cmd ${CONDA_ROOT}/bin/conda info
