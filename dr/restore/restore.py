import logging
import tempfile
import click

import utilslib.library as lib
import utilslib.dr as dr
from utilslib.restore.strategy import KubectlRestoreStrategy


@click.command(name='restore')
@click.option('--bucket', default='bank-app-backup', help='name of the backup bucket', required=True)
@click.option('--clustername', default='cluster1', help='the name of the cluster to restore from', required=True)
@click.option('--kubectl', default='/usr/local/bin/kubectl', help='the path to kubectl', required=True)
@click.option('--dry-run', default=False, help='should we do a dry run')
@click.option('--namespace', default='*', help='the namespace to restore')
@click.option('--log-level', default='INFO', help='the log level')
def restore_command(bucket, clustername, kubectl, dry_run, namespace, log_level):
    """Restore Kubernetes namespaces from a backup in S3"""

    log = logging.getLogger(__name__)
    log.setLevel(log_level)

    log.info("starting restore")

    temp_folder = tempfile.gettempdir()
    log.debug("using temporary directory: %s", temp_folder)

    strategy = KubectlRestoreStrategy(clustername, kubectl, temp_folder, dry_run)

    restore = dr.Restore(bucket_name=bucket, strategy=strategy, log_level=log_level)
    restore.restore_namespaces(clusterName=clustername, namespacesToRestore=namespace)

    log.info("finished restoring")
