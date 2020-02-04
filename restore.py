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
import click

import utilslib.library as lib
import utilslib.dr as dr
from restore import KubectlRestoreStrategy


logging.basicConfig(format='%(asctime)-15s %(name)s:%(lineno)s - ' + 
                    '%(funcName)s() %(levelname)s - %(message)s',
                    level=logging.INFO)
log = logging.getLogger()
log.setLevel(logging.INFO)

@click.command()
@click.option('--bucket', default='bank-app-backup', help='name of the backup bucket', required=True)
@click.option('--clustername', default='cluster1', help='the name of the cluster to restore from', required=True)
@click.option('--kubectl', default='/usr/local/bin/kubectl', help='the path to kubectl', required=True)
@click.option('--dry-run', default=True, help='should we do a dry run')
@click.option('--namespace', default='*', help='the namespace to restore')
def restore(bucket, clustername, kubectl, dry_run, namespace):
    """Restore Kubernetes namespaces from a backup in S3"""
    log.info("starting restore")

    temp_folder = tempfile.gettempdir()

    strategy = KubectlRestoreStrategy(clustername, kubectl, temp_folder, dry_run)

    restore = dr.Restore(bucket_name=bucket, strategy=strategy)
    restore.restore_namespaces(clusterName=clustername, namespacesToRestore=namespace)

    log.info("finished restoring")

if __name__ == '__main__':
    restore()
