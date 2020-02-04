#!/usr/bin/python3
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
if len(sys.argv) < 2:
    log.error("namespace argument required")
    sys.exit(1)
namespace = sys.argv[1]
backup = dr.Backup(loglevel="DEBUG", bucket_name='bank-app-backup')
backup.save_namespace(namespace)