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

backup = dr.Backup(loglevel="DEBUG", bucket_name='bank-app-backup')
excluded_namespaces=["kube-system", "kube-public",  "kube-node-lease", "istio-system"]

namespaces = [n for n in backup.list_namespaces() if n.metadata.name not in excluded_namespaces]

for n in namespaces:
    print("\nbackingup namespace: {}".format(n.metadata.name))
    items = backup.save_namespace(n.metadata.name)

os.environ["KUBECONFIG"] = "/home/pcarlton/c1.yaml"

restore = dr.Restore(loglevel="DEBUG", bucket_name='bank-app-backup')
#log.setLevel(logging.DEBUG)
restore.restore_namespaces()
