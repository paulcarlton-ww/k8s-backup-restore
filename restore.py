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
import tempfile

import utilslib.library as lib
import utilslib.dr as dr
from restore import KubectlRestoreStrategy


logging.basicConfig(format='%(asctime)-15s %(name)s:%(lineno)s - ' + 
                    '%(funcName)s() %(levelname)s - %(message)s',
                    level=logging.INFO)
log = logging.getLogger()
log.setLevel(logging.INFO)

bucket_name = "bank-app-backup"
cluster_name = "cluster1"
kubectl_path = "/usr/local/bin/kubectl"
temp_folder = tempfile.gettempdir()
dry_run = True
namespace_to_restore = "podinfo"

strategy = KubectlRestoreStrategy(cluster_name, kubectl_path, temp_folder, dry_run)

restore = dr.Restore(bucket_name=bucket_name, strategy=strategy)
restore.restore_namespaces(clusterName=cluster_name, namespacesToRestore=namespace_to_restore)

log.info("finished restoring")
