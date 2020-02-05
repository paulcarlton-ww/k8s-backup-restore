#!/usr/bin/python3
"""
Backup utility
"""
from __future__ import print_function
import sys
import os
import time
import logging
import click
from kubernetes import client, config, watch
import utilslib.library as lib
import utilslib.dr as dr

@click.command(name='backup')
@click.option('--bucket', default='bank-app-backup', help='name of the backup bucket', required=True)
@click.option('--namespace', help='the namespace to restore', required=True)
@click.option('--log-level', default='INFO', help='the log level')
def backup_command(bucket, namespace, log_level):
    """Backups Kubernetes namespaces to S3"""

    log = logging.getLogger(__name__)
    log.setLevel(log_level)

    log.info("starting backup")

    backup = dr.Backup(loglevel=log_level, bucket_name=bucket)
    backup.save_namespace(namespace)

    log.info("finished backup")