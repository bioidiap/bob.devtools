#!/usr/bin/env bash

# Installs the relevant SDK

# gets the current path leading to this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"

if [ ! -r "MacOSX${1}.sdk.tar.xz" ]; then
  echo "Downloading macOS ${1} SDK..."
  curl -L -o ${DIR}/MacOSX${1}.sdk.tar.xz https://github.com/phracker/MacOSX-SDKs/releases/download/10.13/MacOSX${1}.sdk.tar.xz
else
  echo "File MacOSX${1}.sdk.tar.xz is already here, skip download"
fi

if [ ! -d /opt ]; then mkdir /opt; fi
cd /opt
tar xfJ "${DIR}/MacOSX${1}.sdk.tar.xz"
ln -s /opt/MacOSX${1}.sdk /Library/Developer/CommandLineTools/SDKs/
