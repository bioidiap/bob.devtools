#!/usr/bin/env bash

# Bootstraps a new conda installation and prepares base environment
# if "local" is passed as parameter, then self installs an already built
# version of bob.devtools available on your conda-bld directory. If you pass
# "beta", then it bootstraps from the package installed on our conda beta
# channel.  If you pass "stable", then it bootstraps installing the package
# available on the stable channel.
#
# If bootstrapping anything else than "build", then provide a second argument
# with the name of the environment that one wants to create with an
# installation of bob.devtools.

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

# merges conda cache folders
# $1: Path to the main cache to keep. The directory must exist.
# $2: Path to the extra cache to be merged into main cache
merge_conda_cache() {
  if [ -e ${1} ]; then
    _cached_urlstxt="${2}/pkgs/urls.txt"
    _urlstxt="${1}/pkgs/urls.txt"
    if [ -e ${2}/pkgs ]; then
      log_info "Merging urls.txt and packages with cached files..."
      mv ${2}/pkgs/*.tar.bz2 ${1}/pkgs
      cat ${_urlstxt} ${_cached_urlstxt} | sort | uniq > ${_urlstxt}
    else
      run_cmd mkdir -p ${1}/pkgs
      run_cmd touch ${1}/pkgs/urls.txt
    fi
    run_cmd touch ${1}/pkgs/urls
    if [ -d ${2}/conda-bld ]; then
      log_info "Moving conda-bld packages (artifacts)..."
      run_cmd mv ${2}/conda-bld ${1}
      run_cmd ${CONDA_ROOT}/bin/conda index --verbose ${1}/conda-bld
      run_cmd ls -l ${1}/conda-bld
      run_cmd ls -l ${1}/conda-bld/noarch/
    fi
  fi
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
  merge_conda_cache ${1} ${1}.cached
  # remove the backup cache folder
  rm -rf ${1}.cached

  # List currently available packages on cache
  # run_cmd ls -l ${1}/pkgs/
  # run_cmd cat ${1}/pkgs/urls.txt

  hash -r
}


check_defined CONDA_ROOT
check_defined CI_PROJECT_DIR

export CONDARC="${CONDA_ROOT}/condarc"
check_defined CONDARC

# checks if a conda installation exists. Otherwise, installs one
if [ ! -e ${CONDA_ROOT}/bin/conda ]; then
  install_miniconda ${CONDA_ROOT}
fi

run_cmd cp -fv ${CI_PROJECT_DIR}/bob/devtools/data/base-condarc ${CONDARC}
echo "Contents of \`${CONDARC}':"
cat ${CONDARC}

# setup conda-channels
CONDA_CHANNEL_ROOT="http://www.idiap.ch/public/conda"
check_defined CONDA_CHANNEL_ROOT
CONDA_CLI_CHANNELS="-c ${CONDA_CHANNEL_ROOT} -c defaults"

# creates a base installation depending on the purpose
if [ "${1}" == "build" ]; then
  run_cmd ${CONDA_ROOT}/bin/conda install -n base python conda=4 conda-build=3
elif [ "${1}" == "local" ]; then
  CONDA_CLI_CHANNELS="-c ${CONDA_ROOT}/conda-bld ${CONDA_CLI_CHANNELS}"
  run_cmd ls -l ${CONDA_ROOT}/conda-bld
  run_cmd ls -l ${CONDA_ROOT}/conda-bld/noarch/
  run_cmd ${CONDA_ROOT}/bin/conda create -n "${2}" --override-channels ${CONDA_CLI_CHANNELS} bob.devtools
elif [ "${1}" == "beta" ] || [ "${1}" == "stable" ]; then
  run_cmd ${CONDA_ROOT}/bin/conda create -n "${2}" --override-channels ${CONDA_CLI_CHANNELS} bob.devtools
else
  log_error "Bootstrap with 'build', or 'local|beta|stable <name>'"
  log_error "The value '${1}' is not currently supported"
  exit 1
fi

# cleans up
run_cmd ${CONDA_ROOT}/bin/conda clean --lock

# print conda information for debugging purposes
run_cmd ${CONDA_ROOT}/bin/conda info