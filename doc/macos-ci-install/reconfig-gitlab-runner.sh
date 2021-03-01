#!/usr/bin/env bash

set -x

if [[ $EUID == 0 ]]; then
  # restarts to reconfigure as gitlab user
  exec su gitlab -c "$(which bash) ${0}"
fi

# the command above is bogus - it will use the "admin" user home dir
# you need to reconfigure it to fix this
cfgfile="/Users/gitlab/Library/LaunchAgents/homebrew.mxcl.gitlab-runner.plist"
/bin/launchctl stop $cfgfile
/bin/launchctl unload $cfgfile
/usr/bin/sed -i~ 's/admin/gitlab/g' $cfgfile
/bin/launchctl load $cfgfile
/bin/launchctl start $cfgfile
