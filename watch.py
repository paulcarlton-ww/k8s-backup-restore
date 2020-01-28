#!/usr/bin/python3
"""
Watch
"""
from __future__ import print_function
import sys
import os
import time
import logging
from kubernetes import client, config, watch
import utilslib.library as lib

log = logging.getLogger()
log.setLevel(logging.DEBUG)

sys.path.insert(0, "/home/pcarlton/pylib/site-packages")

config.load_kube_config()

v1 = client.CoreV1Api()
v1ext = client.ExtensionsV1beta1Api()

def watch_it():
    v1 = client.CoreV1Api()
    watcher = watch.Watch()
    for e in watcher.stream(v1.list_namespaced_config_map, "default", resource_version=0):
        type = e['type']
        object = e['object']  # object is one of type return_type
        raw_object = e['raw_object']  # raw_object is a dict
        log.info("Event: %s %s %s" % (e['type'], e['object'].kind, e['object'].metadata.name))

watch_it()