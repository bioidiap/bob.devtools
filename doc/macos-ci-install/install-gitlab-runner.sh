#!/usr/bin/env bash
set -eox pipefail
LOCATION=/usr/local/bin/gitlab-runner
curl --output ${LOCATION} https://gitlab-runner-downloads.s3.amazonaws.com/latest/binaries/gitlab-runner-darwin-amd64
chmod +x ${LOCATION}
