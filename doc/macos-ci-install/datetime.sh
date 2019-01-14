#!/usr/bin/env bash

#    run more easily.
# -e will cause the script to exit immediately if any command within it exits non 0
# -o pipefail : this will cause the script to exit with the last exit code run.
#               In tandem with -e, it will return the exit code of the first
#               failing command.
set -eox pipefail

systemsetup -setusingnetworktime on
systemsetup -settimezone Europe/Zurich
systemsetup -setnetworktimeserver time.euro.apple.com.

