# coding: utf-8
"""
This module contains DR classes
"""

__author__ = "Paul Carlton <paul.carlton414@gmail.com>"
__copyright__ = "Copyright (C) 2016 Paul Carlton"
__license__ = "Public Domain"
__version__ = "0.2"
__date__ = "18 October 2016"


from datetime import date, timedelta
import os
import sys
import time
import functools

import boto3
import boto3.s3
from botocore.config import Config
import json
from kubernetes import client, config
import utilslib.library as lib
import logging

logging.basicConfig(format='%(asctime)-15s %(name)s:%(lineno)s - ' + 
                    '%(funcName)s() %(levelname)s - %(message)s',
                    level=logging.INFO)
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

class Base(object):
    log = None
    
    @lib.retry_wrapper
    def __init__(self, *args, **kwargs):
        """
        Constructor

        Args:
        args     -- posistional arguments
        kwargs   -- Named arguments

        Returns:
        Base object
        """
        super(Base, self).__init__()
        log_name = kwargs["logname"] if "logname" in kwargs else __name__
        log = logging.getLogger(log_name)
        log_level = kwargs["loglevel"] if "loglevel" in kwargs else "CRITICAL"
        loglevel = getattr(logging, log_level, logging.CRITICAL)
        log.setLevel(loglevel)
            
class S3(Base):
    s3 = None
    bucket = None
        
    @lib.retry_wrapper
    def __init__(self, *args, **kwargs):
        """
        Constructor

        Args:
        args     -- posistional arguments
        kwargs   -- Named arguments

        Returns:
        K8s object
        """
        super(S3, self).__init__(*args, **kwargs)
        config = Config(connect_timeout=5, retries={'max_attempts': 0})
        self.s3 = boto3.resource('s3', config=config)
        bucket_name = kwargs.get("bucket_name", None)
        if bucket_name is not None:
            self.bucket = self.s3.Bucket(bucket_name)
    
    @staticmethod
    def parse_key(key):
        """
        parses the S3 bucket key returning component parts

        Args:
        key   -- the key

        Returns:
        tuble containing the fields in the key based on '/' seperator.
        """
        fields = key.split('/')
        if len(fields) != 4:
            raise Exception(
                "key should comprise /namespaces/namespace/kind/name")
        return fields[1], fields[2], fields[3]
 
class Store(S3):

    @lib.retry_wrapper
    def __init__(self, *args, **kwargs):
            """
            Constructor

            Args:
            args     -- posistional arguments
            kwargs   -- Named arguments

            Returns:
            Store object
            """
            super(Store, self).__init__(*args, **kwargs)

    @lib.timing_wrapper
    @lib.retry_wrapper       
    def store_in_bucket(self, key, data):
        """
        store data in an S3 bucket with the provided key.

        :param key: The key.
        :param data: The dictionary to store
        """ 
        self.bucket.put_object(Key=key,
                               Body=json.dumps(data, cls=lib.DateTimeEncoder))

class Retrieve(S3):
    
    @lib.retry_wrapper
    def __init__(self, *args, **kwargs):
            """
            Constructor

            Args:
            args     -- posistional arguments
            kwargs   -- Named arguments

            Returns:
            Retrieve object
            """
            super(Retrieve, self).__init__(*args, **kwargs)
    
    @lib.timing_wrapper
    @lib.retry_wrapper       
    def get_bucket_items(self, prefix):
        """
        retrieve items in an S3 bucket with the provided prefix.

        :param prefix: The key prefix .
        """

        for obj in list(self.bucket.objects.filter(Prefix=prefix)):
            yield(obj.key, json.loads(obj.get()['Body'].read()))
      

class K8s(object):
    v1 = None
    v1App = None
    v1ext = None
    
    kinds = {'ConfigMap': ('v1', 'config_map'),
             'EndPoints': ('v1', 'endpoints'),
             'Event': ('v1', 'event'),
             'LimitRange': ('v1', 'limit_range'),
             'PersistentVolumeClaim': ('v1', 'persistent_volume_claim'),
             'ResourceQuota': ('v1', 'resource_quota'),
             'Secret': ('v1', 'secret'),
             'Service': ('v1', 'service'),
             #'ServiceAccount': ('v1', 'service_account'),
             'PodTemplate': ('v1', 'pod_template'),
             'Pod': ('v1', 'pod'),
             'ReplicationController': ('v1', 'replication_controller'),
             'ControllerRevision': ('v1App', 'controller_revision'),
             'DaemonSet': ('v1App', 'daemon_set'),
             'ReplicaSet': ('v1App', 'replica_set'),
             'StatefulSet': ('v1App', 'stateful_set'),
             'Deployment': ('v1App', 'deployment')}
    
    @lib.retry_wrapper
    def __init__(self, *args, **kwargs):
        """
        Constructor

        Args:
        args     -- posistional arguments
        kwargs   -- Named arguments

        Returns:
        K8s object
        """
        super(K8s, self).__init__(*args, **kwargs)
        # Use in cluster config when deployed to cluster
        config.load_kube_config()
        self.v1 = client.CoreV1Api()
        self.v1App = client.AppsV1Api()
        self.v1ext = client.ExtensionsV1beta1Api()

    def get_api_method(self, kind):
        try:
            api_name = K8s.kinds.get(kind)[0]
            method = K8s.kinds.get(kind)[1]
            api = getattr(self, api_name)
        except Exception as e:
            raise e
        return api, method
            
            
    @lib.timing_wrapper
    @lib.k8s_chunk_wrapper
    @lib.retry_wrapper
    def list_namespaces(self, limit=2, next=''):
        return self.v1.list_namespace(limit=limit, _continue=next)
 
    @lib.timing_wrapper
    @lib.k8s_chunk_wrapper
    @lib.retry_wrapper
    def list_kind(self, namespace, kind, limit=2, next=''):
        api, method = self.get_api_method(kind)
        return lib.dynamic_method_call(namespace, limit=limit, _continue=next,
                                   method_text=method,
                                   method_prefix="list_namespaced_",
                                   method_object=api)
        
    @lib.timing_wrapper
    @lib.retry_wrapper
    def read_kind(self, namespace, kind, name):
        api, method = self.get_api_method(kind)
        return lib.dynamic_method_call(name, namespace,
                                   method_text=method,
                                   method_prefix="read_namespaced_",
                                   method_object=api)

    @lib.timing_wrapper
    @lib.retry_wrapper
    def delete_kind(self, namespace, kind, name):
        api, method = self.get_api_method(kind)
        return lib.dynamic_method_call(name, namespace,
                                   method_text=method,
                                   method_prefix="delete_namespaced_",
                                   method_object=api)
     
    @lib.timing_wrapper
    @lib.retry_wrapper
    def create_kind(self, namespace, kind, data):
        api, method = self.get_api_method(kind)
        return lib.dynamic_method_call(namespace, data,
                                   method_text=method,
                                   method_prefix="create_namespaced_",
                                   method_object=api)
          
    @lib.timing_wrapper
    @lib.retry_wrapper
    def replace_kind(self, namespace, kind, name, data):
        api, method = self.get_api_method(kind)
        return lib.dynamic_method_call(name, namespace, data,
                                   method_text=method,
                                   method_prefix="replace_namespaced_",
                                   method_object=api)
  
class Backup(K8s, Store):
    
    @lib.retry_wrapper
    def __init__(self, *args, **kwargs):
        """
        Constructor

        Args:
        args     -- posistional arguments
        kwargs   -- Named arguments

        Returns:
        Backup object
        """
        super(Backup, self).__init__(*args, **kwargs)
    
    @staticmethod
    def prepare_item(kind, data):
        d = data.to_dict()
        [d['metadata'].pop(x, None) for x in ['cluster_name',
                                              'creation_timestamp', 
                                              'deletion_grace_period_seconds',
                                              'deletion_timestamp',
                                              'finalizers',
                                              'string_data',
                                              'generate_name',
                                              'generation',
                                              'initializers',
                                              'managed_fields', 
                                              'owner_references',
                                              'resource_version'
                                              'uid', 'self_link']]
        key = "namespaces/{}/{}/{}".format(d['metadata']['namespace'], 
                                           kind, d['metadata']['name'])
        return key, d
    
    @lib.timing_wrapper
    def save_namespace(self, namespace):
        for kind in K8s.kinds.keys():
            for item in self.list_kind(namespace, kind):
                read_data = self.read_kind(namespace, kind, item.metadata.name)
                key, data = Backup.prepare_item(kind, read_data)
                self.store_in_bucket(key, data)


class Restore(K8s, Retrieve):

    @lib.retry_wrapper
    def __init__(self, *args, **kwargs):
        """
        Constructor

        Args:
        args     -- posistional arguments
        kwargs   -- Named arguments

        Returns:
        Restore object
        """
        super(Restore, self).__init__(*args, **kwargs)
    
    
    @lib.timing_wrapper
    def remove_if_exists(self, namespace, kind, name):
        try:
            self.read_kind(namespace, kind, name)
        except Exception as e:
            return
        self.delete_kind(namespace, kind, name)
                
    @lib.timing_wrapper
    def restore_namespaces(self, namespace=""):
        prefix = "namespaces/{}".format(namespace)
        for key, data in self.get_bucket_items(prefix):
            namespace, kind, name = S3.parse_key(key)
            #self.replace_kind(namespace, kind, name, data)
            self.remove_if_exists(namespace, kind, name)
            self.create_kind(namespace, kind, data)
