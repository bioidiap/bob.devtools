#!/usr/bin/env bash
# Wed Jan  9 16:48:57 CET 2019

source $(dirname ${0})/functions.sh

run_cmd cp -fv ${CI_PROJECT_DIR}/bob/devtools/data/base-condarc ${CONDARC}
echo "channels:" >> ${CONDARC}
echo "  - ${DOCSERVER}/public/conda" >> ${CONDARC}
echo "  - defaults" >> ${CONDARC}

deploy_conda_packages ${CONDA_CHANNELS[0]} ${CI_PROJECT_NAME}

# upload the docs from the sphinx folder (usually an artifact of Linux Python
# 3.6 builds)
for folder in "${DOC_UPLOADS[@]}"; do
  dav_upload_folder sphinx "${folder}"
done
