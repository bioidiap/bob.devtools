#!/bin/bash

set -eox pipefail

# read into array ${RECOMMENDED[@]}, a filtered list of available and
# recommended software updates
self=`basename $0`
TMPFILE=`mktemp -t ${self}` || exit 1
softwareupdate -l | grep -e '^\s\+\*' | sed -e 's/^[ \*]*//g' > ${TMPFILE}

# starts of strings of installables we don't care about
BLACKLIST=()
BLACKLIST+=('iBook')
BLACKLIST+=('iTunes')
BLACKLIST+=('Install macOS')

cat ${TMPFILE} | while read k; do
  update="yes"
  for l in "${BLACKLIST[@]}"; do
    if [[ "${k}" == ${l}* ]]; then
      update="no"
    fi
  done
  if [[ "${update}" == "yes" ]]; then
    echo "Updating $k..."
    touch /tmp/.com.apple.dt.CommandLineTools.installondemand.in-progress
    softwareupdate --verbose --install "${k}"
    rm /tmp/.com.apple.dt.CommandLineTools.installondemand.in-progress
  else
    echo "Ignoring update for $k..."
    softwareupdate --ignore "${k}"
  fi
done
rm -f ${TMPFILE}

# We don't want our system changing on us or restarting to update. Disable
# automatic updates.
echo "Disable automatic updates…"
softwareupdate --schedule off
