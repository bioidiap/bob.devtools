#!/usr/bin/env bash
# Tue 16 Jan 11:15:32 2018 CET

source $(dirname ${0})/functions.sh

# checks if a conda installation exists. Otherwise, install one
if [ ! -e ${CONDA_ROOT}/bin/conda ]; then
  install_miniconda ${CONDA_ROOT}
fi

mkdir -p ${CONDA_ROOT}/pkgs
touch ${CONDA_ROOT}/pkgs/urls
touch ${CONDA_ROOT}/pkgs/urls.txt

create_condarc ${CONDARC}

set_conda_channels ${CI_COMMIT_TAG}
for k in "${CONDA_CHANNELS[@]}"; do
  echo "  - ${DOCSERVER}/${k}" >> ${CONDARC}
done
echo "  - defaults" >> ${CONDARC}

# displays contents of our configuration
echo "Contents of \`${CONDARC}':"
cat ${CONDARC}

# updates conda installation
run_cmd ${CONDA_ROOT}/bin/conda install python conda=4 curl conda-build=3

# cleans up
run_cmd ${CONDA_ROOT}/bin/conda clean --lock

# print conda information for debugging purposes
run_cmd ${CONDA_ROOT}/bin/conda info
