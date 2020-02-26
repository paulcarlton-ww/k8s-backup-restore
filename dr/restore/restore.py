import logging
import tempfile
import click

import utilslib.library as lib
import utilslib.dr as dr
from utilslib.restore.strategy import KubectlRestoreStrategy


@click.command(name='restore')
@click.option('--clusterset', default='default', help='the name of the cluster to restore from', required=True)
@click.option('--clustername', default='cluster1', help='the name of the cluster to restore from', required=True)
@click.option('--kubectl', default='/usr/local/bin/kubectl', help='the path to kubectl', required=True)
@click.option('--dry-run', default=False, help='should we do a dry run')
@click.option('--namespace', default='*', help='the namespace to restore')
@click.option('--bucket', default='bank-apps-backup', help='name of the backup bucket')
@click.option('--log-level', default='INFO', help='the log level')
@click.option('--kube-config', help='the kube config file of the destination cluster', required=True)
def restore_command(bucket, clusterset, clustername, kubectl, dry_run, namespace, log_level, kube_config):
    """Restore Kubernetes namespaces from a backup in S3"""
    lib.log.info("starting restore")

    temp_folder = tempfile.gettempdir()
    lib.log.debug("using temporary directory: %s", temp_folder)

    strategy = KubectlRestoreStrategy(clustername, kubectl, temp_folder, dry_run)

    restore = dr.Restore(bucket_name=bucket, strategy=strategy, log_level=log_level, kube_config=kube_config)
    restore.restore_namespaces(clusterset, clustername, namespace)

    lib.log.info("finished restoring")
