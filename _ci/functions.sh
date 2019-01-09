#!/usr/bin/env bash
# Wed  9 Jan 2019 14:33:20 CET

# Build utilities
SCRIPTS_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

# Determines the operating system we're using
osname() {
  [[ "$(uname -s)" == "Darwin" ]] && echo "osx" || echo "linux"
}

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


# Logs a given environment variable to the screen
log_env() {
  log_info "${1}=${!1}"
}


# Checks a given environment variable is set (non-zero size)
check_env() {
  check_defined "${1}"
  log_env "${1}"
}


# Checks a given environment variable array is set (non-zero size)
# Then prints all of its components
check_array_env() {
  check_defined "${1}"
  eval array=\( \${${1}[@]} \)
  for i in "${!array[@]}"; do
    log_info "${1}[${i}]=${array[${i}]}";
  done
}


# Exports a given environment variable, verbosely
export_env() {
  check_defined "${1}"
  export ${1}
  log_info "export ${1}=${!1}"
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


if [ -z "${BOB_PACKAGE_VERSION}" ]; then
  if [ ! -r "version.txt" ]; then
    log_error "./version.txt does not exist - cannot figure out version number"
    exit 1
  fi
  BOB_PACKAGE_VERSION=`cat version.txt | tr -d '\n'`;
fi


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


# installs a miniconda installation.
# $1: Path to where to install miniconda.
install_miniconda() {
  log_info "Installing miniconda in ${1} ..."

  # downloads the latest conda installation script
  if [ "${OSNAME}" == "linux" ]; then
    object=https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh
  else
    object=https://repo.continuum.io/miniconda/Miniconda3-latest-MacOSX-x86_64.sh
  fi

  # checks if miniconda.sh exists
  if [ ! -e miniconda.sh ]; then
    log_info "Downloading latest miniconda3 installer..."
    run_cmd curl --silent --output miniconda.sh ${object}
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


# Creates a sane base condarc file
# $1: Path to where to populate the condarc file
create_condarc() {
  log_info "Populating the basic condarc file in ${1} ..."

  cat <<EOF > ${1}
default_channels: #!final
  - https://repo.anaconda.com/pkgs/main
  - https://repo.anaconda.com/pkgs/free
  - https://repo.anaconda.com/pkgs/r
  - https://repo.anaconda.com/pkgs/pro
add_pip_as_python_dependency: false #!final
changeps1: false #!final
always_yes: true #!final
quiet: true #!final
show_channel_urls: true #!final
anaconda_upload: false #!final
ssl_verify: false #!final
channels: #!final
EOF

}


# sets CONDA_CHANNELS to the list of conda channels that should be considered
# $2: typically, the value of ${CI_COMMIT_TAG} or empty
# given the current visibility/tagging conditions of the package.
set_conda_channels() {
  CONDA_CHANNELS=() #resets bash array
  if [ -z "${1}" ]; then #public beta build
    CONDA_CHANNELS+=('public/conda/label/beta')
    CONDA_CHANNELS+=('public/conda')
  else #public (tagged) build
    CONDA_CHANNELS+=('public/conda')
  fi
  check_array_env CONDA_CHANNELS
}


log_env PYTHON_VERSION
check_env CI_PROJECT_DIR
check_env CI_PROJECT_NAME
check_env CI_COMMIT_REF_NAME
export_env BOB_PACKAGE_VERSION

# Sets up variables
OSNAME=`osname`
check_env OSNAME

DOCSERVER=http://www.idiap.ch

# Sets up the location of our rc file for conda
CONDARC=${CONDA_ROOT}/condarc

if [ -z "${OS_SLUG}" ]; then
  OS_SLUG="${OSNAME}-64"
fi

export_env OS_SLUG
export_env DOCSERVER
check_env CONDA_ROOT
export_env CONDARC

# Sets up certificates for curl and openssl
CURL_CA_BUNDLE="${CI_PROJECT_DIR}/bob/devtools/data/cacert.pem"
export_env CURL_CA_BUNDLE
SSL_CERT_FILE="${CURL_CA_BUNDLE}"
export_env SSL_CERT_FILE
GIT_SSL_CAINFO="${CURL_CA_BUNDLE}"
export_env GIT_SSL_CAINFO

# Sets up upload folders for documentation (just in case we need them)
# See: https://gitlab.idiap.ch/bob/bob.admin/issues/2

# Sets up the language so Unicode filenames are considered correctly
LANG="en_US.UTF-8"
LC_ALL="${LANG}"
export_env LANG
export_env LC_ALL
