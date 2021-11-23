#!/usr/bin/env bash

# Update CI installation
brew=/usr/local/bin/brew
pip=/usr/local/bin/pip3
if [ ! -x ${brew} ]; then
    brew=/opt/homebrew/bin/brew
    pip=/opt/homebrew/bin/pip3
fi
echo "[update-ci.sh] Updating homebrew..."
${brew} update

echo "[update-ci.sh] Upgrading homebrew (outdated) packages..."
${brew} upgrade

# A cask upgrade may require sudo, so we cannot do this
# with an unattended setup
#echo "[update-ci.sh] Updating homebrew casks..."
#${brew} cask upgrade

echo "[update-ci.sh] Cleaning-up homebrew..."
${brew} cleanup

# Updates PIP packages installed
function pipupdate() {
  echo "[update-ci.sh] Updating ${1} packages..."
  [ ! -x "${1}" ] && return
  ${1} list --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1  | xargs -n1 ${1} install -U;
}

pipupdate ${pip}
