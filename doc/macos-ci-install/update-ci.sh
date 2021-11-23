#!/usr/bin/env bash

# Update CI installation
echo "[update-ci] Updating homebrew..."
brew=/usr/local/bin/brew
pip=/usr/local/bin/pip3
if [ ! -x ${brew} ]; then
    brew=/opt/homebrew/bin/brew
    pip=/opt/homebrew/bin/pip3
fi
${brew} update

# We now check if gitlab-runner is going to be updated
gitlab_runner_reconfigure=false
if [[ $(brew outdated | grep -c "gitlab-runner") != 0 ]]; then
    echo "[update-ci] The package gitlab-runner is going to be updated (will reconfigure)"
    gitlab_runner_reconfigure=true
fi

echo "[update-ci] Upgrading homebrew (outdated) packages..."
${brew} upgrade

# A cask upgrade may require sudo, so we cannot do this
# with an unattended setup
#echo "Updating homebrew casks..."
#${brew} cask upgrade

echo "[update-ci] Cleaning-up homebrew..."
${brew} cleanup

# Updates PIP packages installed
function pipupdate() {
  echo "Updating ${1} packages..."
  [ ! -x "${1}" ] && return
  ${1} list --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1  | xargs -n1 ${1} install -U;
}

pipupdate ${pip}

# If gitlab-runner was updated, re-configures it
if [[ "${gitlab_runner_reconfigure}" == "true" ]]; then
    echo "[update-ci] Reconfiguring gitlab-runner..."
    /bin/bash <(curl -s https://gitlab.idiap.ch/bob/bob.devtools/raw/master/doc/macos-ci-install/reconfig-gitlab-runner.sh)
    echo "[update-ci] The gitlab-runner daemon should be fully operational now."
fi
