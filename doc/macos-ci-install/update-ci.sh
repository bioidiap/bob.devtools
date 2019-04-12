#!/usr/bin/env bash

# Update CI installation
echo "Updating homebrew..."
brew=/usr/local/bin/brew
${brew} update
${brew} upgrade
${brew} cleanup


# Updates PIP packages installed
function pipupdate() {
  echo "Updating ${1} packages..."
  [ ! -x "${1}" ] && return
  ${1} list --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1  | xargs -n1 ${1} install -U;
}

pipupdate /usr/local/bin/pip3
pipupdate /usr/local/bin/pip2
