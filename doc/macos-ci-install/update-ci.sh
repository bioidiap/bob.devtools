#!/usr/bin/env bash

# Update CI installation
echo "Updating homebrew..."
brew=/usr/local/bin/brew
if [ ! -x ${brew} ]; then
    brew=/opt/homebrew/bin/brew
fi
${brew} update
${brew} upgrade

# A cask upgrade may require sudo, so we cannot do this
# with an unattended setup
#echo "Updating homebrew casks..."
#${brew} cask upgrade

${brew} cleanup

# Updates PIP packages installed
function pipupdate() {
  echo "Updating ${1} packages..."
  [ ! -x "${1}" ] && return
  ${1} list --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1  | xargs -n1 ${1} install -U;
}

pip=/usr/local/bin/pip3
if [ ! -x ${pip} ]; then
    brew=/opt/homebrew/bin/pip3
fi
pipupdate ${pip}
