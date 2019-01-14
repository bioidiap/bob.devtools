#!/usr/bin/env bash

# Installs basic software on a fresh macOS installation that requires admin
# priviledges.

# VARIABLES - edit to your requirements
MACOS_VERSION="${1}"
USERNAME="${2}"

# --------------------
# Don't edit past this
# --------------------

# gets the current path leading to this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"

echo "Setting up date and time..."
${DIR}/datetime.sh

echo "Updating the current system and disabling automatic updates..."
${DIR}/system-update.sh

echo "Installing Xcode Command-Line (CLI) tools..."
${DIR}/xcode-cli-tools.sh

echo "Installing macOS ${MACOS_VERSION} SDK..."
${DIR}/install-sdk.sh ${MACOS_VERSION}

echo "Setting up special idiap.ch host..."
${DIR}/idiap-host.sh

echo "Installing homebrew and build-time dependencies...":w
${DIR}/setup-paths.sh
${DIR}/install-homebrew.sh ${USER}

echo "Installing (or updating) gitlab runner..."
{DIR}/install-gitlab-runner.sh
