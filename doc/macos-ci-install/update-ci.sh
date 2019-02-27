#!/usr/bin/env bash

# Update CI installation
echo "Updating homebrew..."
brew=/usr/local/bin/brew
${brew} update
${brew} upgrade
${brew} cleanup

echo "Updating python packages..."
pip=/usr/local/bin/pip3
${pip} list --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1  | xargs -n1 ${pip} install -U
