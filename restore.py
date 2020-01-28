#!/usr/bin/python
"""
Backup utility
"""
from __future__ import print_function
import sys
import os
import time
import logging
from kubernetes import client, config, watch
import utilslib.library as lib
import utilslib.dr as dr

log = logging.getLogger()
log.setLevel(logging.INFO)

restore = dr.Restore(loglevel="DEBUG", bucket_name='bank-app-backup')
#log.setLevel(logging.DEBUG)
restore.restore_namespaces()
