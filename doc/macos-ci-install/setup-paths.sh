#!/usr/bin/env bash

set -x

# changes path setup for all users, puts homebrew first
sed -e '/^\/usr\/local/d' -i .orig /etc/paths
sed -e '/^\/Library\/TeX\/texbin/d' -i .orig /etc/paths
echo -e "/usr/local/bin\n/usr/local/sbin\n/usr/local/opt/coreutils/libexec/gnubin\n/Library/TeX/texbin\n$(cat /etc/paths)" > /etc/paths

# ensures no cross-talking happens between miniconda installations on
# the shared builder - see bob/bob.devtools#12 and bob/bob.devtools!8
condadir=/Users/${USER}/.conda
mkdir ${condadir}
touch ${condadir}/environments.txt
chown -R ${USER}:staff ${condadir}
chmod a-w ${condadir}/environments.txt
