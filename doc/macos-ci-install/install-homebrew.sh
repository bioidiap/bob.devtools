#!/usr/bin/env bash

set -x

if [[ $EUID == 0 ]]; then
  # changes path setup for all users, puts homebrew first
  sed -e '/^\/usr\/local/d' -i .orig /etc/paths
  echo -e "/usr/local/bin\n/usr/local/sbin\n/usr/local/opt/coreutils/libexec/gnubin\n$(cat /etc/paths)" > /etc/paths

  # restarts to install brew as non-root user
  exec su ${1} -c "$(which bash) ${0}"
fi

ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)" </dev/null
brew=/usr/local/bin/brew

${brew} install curl git coreutils bash-completion highlight neovim tmux htop python@3
${brew} link --force curl #keg-only recipe
${brew} cask install mactex

# LaTeX slides/beamer dependencies
pip=/usr/local/bin/pip3
${pip} install pygments
