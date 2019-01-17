#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Environment variable initialization'''

import os
from .constants import CACERT
from .bootstrap import set_environment


# must set LANG and LC_ALL before using click
set_environment('LANG', 'en_US.UTF-8', os.environ)
set_environment('LC_ALL', os.environ['LANG'], os.environ)

# we need the right certificates setup as well
set_environment('SSL_CERT_FILE', CACERT, os.environ)
set_environment('REQUESTS_CA_BUNDLE', CACERT, os.environ)
