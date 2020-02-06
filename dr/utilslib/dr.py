"""
This module contains DR classes
"""

from datetime import date, timedelta
import os
import io
import sys
import time
import functools

import boto3
import boto3.s3
from botocore.config import Config
import json
import yaml
from kubernetes import client, config, utils
from kubernetes.client.rest import ApiException
import utilslib.library as lib
import logging
import tempfile


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
        self.log = logging.getLogger(log_name)
        log_level = kwargs["loglevel"] if "loglevel" in kwargs else "CRITICAL"
        loglevel = getattr(logging, log_level, logging.CRITICAL)
        self.log.setLevel(loglevel)


class S3(Base):
    client = None
    bucket = None
    bucket_name = None

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
        s3 = boto3.resource('s3', config=config)
        self.client = boto3.client('s3')
        self.bucket_name = kwargs.get("bucket_name", None)
        if self.bucket_name is not None:
            self.bucket = s3.Bucket(self.bucket_name)

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
        if len(fields) == 5:
            return fields[0], fields[1], fields[2], fields[4]
        else:
            raise Exception(
                "key should comprise cluster/namespace/kind/apiversion/name")


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
        self.bucket.put_object(Key=key, Body=data)


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
    def get_s3_namespaces(self, prefix):
        """
        retrieve namespace names for provided cluster name prefix.

        :param prefix: The key prefix .
        """
        result = self.client.list_objects(Bucket=self.bucket_name,
                                          Prefix="{}/".format(prefix), Delimiter='/')
        for o in result.get('CommonPrefixes'):
            cluster_namespace = o.get('Prefix')
            yield(cluster_namespace.split('/')[1])

    @lib.timing_wrapper
    @lib.retry_wrapper
    def get_bucket_items(self, prefix):
        """
        retrieve items in an S3 bucket with the provided prefix.

        :param prefix: The key prefix .
        """

        for obj in list(self.bucket.objects.filter(Prefix=prefix)):
            yield(obj.key, obj.get()['Body'].read())


class K8s(object):
    v1 = None
    v1App = None
    v1ext = None
    cluster_name = None

    kinds = {'ConfigMap': ('v1', 'config_map'),
             'LimitRange': ('v1', 'limit_range'),
             'ResourceQuota': ('v1', 'resource_quota'),
             'Secret': ('v1', 'secret'),
             'Service': ('v1', 'service'),
             'PodTemplate': ('v1', 'pod_template'),
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
        cfg = config.kube_config.list_kube_config_contexts()
        self.cluster_name = cfg[0][0]['context']['cluster'].split("/")[1]
        self.v1 = client.CoreV1Api()
        self.v1App = client.AppsV1Api()
        self.v1ext = client.ExtensionsV1beta1Api()
        self.v1beta1 = client.ApiextensionsV1beta1Api()

    @staticmethod
    def strip_nulls(data):
        return {k: v for k, v in data.items() if v is not None}

    @staticmethod
    def strip_underscores(data):
        return {k: v for k, v in data.items() if not k.startswith("_")} 

    @staticmethod
    def process_dict(d):
        [d.pop(x, None) for x in ['clusterName',
                                  'generateName',
                                  'creationTimestamp', 
                                  'deletionGracePeriodSeconds',
                                  'deletionTimestamp',
                                  'finalizers',
                                  'stringData',
                                  'generation',
                                  'initializers',
                                  'managedFields', 
                                  'ownerReferences',
                                  'resourceVersion',
                                  'uid',
                                  'selfLink',
                                  'status']]
        d = K8s.strip_nulls(d)
        d = K8s.strip_underscores(d)
        return d

    @staticmethod
    def object_to_dict(data):
        if isinstance(data, object) and hasattr(data, "attribute_map"):
            d = {}
            for k, v in data.attribute_map.items():
                d[v] = getattr(data, k)
        else:
            if not isinstance(data, dict):
                return data
            if "attribute_map" in data:
                d = {}
                map = data.get("attribute_map", {})
                for k, v in map.items():
                    value = data.pop(k, None)
                    if value:
                        d[v] = value
            else:
                d = data
        return K8s.process_dict(d)

    @staticmethod
    def process_data(data):
        d = K8s.object_to_dict(data)
        if isinstance(d, dict):
            for k, v in d.items():
                d[k] = K8s.process_data(v)
        if isinstance(d, list):
            l = []
            for i in d:
                l.append(K8s.process_data(i))
            d = l
        return d

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
    def list_custom_resource_definition(self, limit=100, next=''):
        return self.v1beta1.list_custom_resource_definition()

    @lib.timing_wrapper
    @lib.retry_wrapper
    def read_resource_definition(self, name):
        return self.v1beta1.list_custom_resource_definition(name=name)

    @lib.timing_wrapper
    @lib.retry_wrapper
    def get_custom_resource_definitions(self):
        for resource in self.list_custom_resource_definition():
            yield self.v1beta1.read_custom_resource_definition(resource.metadata.name)

    @lib.timing_wrapper
    @lib.k8s_chunk_wrapper
    @lib.retry_wrapper
    def list_namespaces(self, limit=100, next=''):
        return self.v1.list_namespace(limit=limit, _continue=next)

    @lib.timing_wrapper
    @lib.retry_wrapper
    def read_namespace(self, namespace):
        return self.v1.read_namespace(namespace)

    @lib.timing_wrapper
    @lib.k8s_chunk_wrapper
    @lib.retry_wrapper
    def list_kind(self, namespace, kind, limit=100, next=''):
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

    custom_resources = []

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

    def create_key_yaml(self, data):
        d = K8s.process_data(data)
        y = yaml.dump(d)
        key = "{}/{}/{}/{}/{}.yaml".format(self.cluster_name,
                                d['metadata']['namespace'] if d["kind"] != "Namespace" else d['metadata']['name'],
                                d["kind"], d["apiVersion"].replace("/", "_"),
                                d['metadata']['name'])
        print("\n# key: {}\n{}".format(key, y))
        return key, y

    @lib.timing_wrapper
    def get_custom_resources(self):
        resources = []
        for resource in self.get_custom_resource_definitions():
            resources.append(resource)

    @lib.timing_wrapper
    def save_namespace(self, namespace):
        ns = self.read_namespace(namespace)
        key, data = self.create_key_yaml(ns)
        self.store_in_bucket(key, data)
        for kind in K8s.kinds.keys():
            for item in self.list_kind(namespace, kind):
                read_data = self.read_kind(namespace, kind, item.metadata.name)
                key, data = self.create_key_yaml(read_data)
                self.store_in_bucket(key, data)


class Restore(K8s, Retrieve):
    kind_order = ['Namespace',
                  'LimitRange',
                  'ResourceQuota',
                  'ConfigMap',
                  'Secret',
                  'Service',
                  'Deployment']

    exclude_list = [("default", "Service", "kubernetes"),
                    ("default", "Endpoints", "kubernetes")]

    @lib.retry_wrapper
    def __init__(self, bucket_name, strategy, log_level):
        super(Restore, self).__init__(bucket_name=bucket_name, loglevel=log_level)
        self.bucket_name = bucket_name
        self.strategy = strategy

    @staticmethod
    def exclude_check(namespace, kind, name):
        if (namespace, kind, name) in Restore.exclude_list:
            return True
        if kind == "Secret" and "default" in name:
            return True
        return False

    @lib.timing_wrapper
    def remove_if_exists(self, namespace, kind, name):
        try:
            self.read_kind(namespace, kind, name)
        except Exception:
            return
        self.delete_kind(namespace, kind, name)

    @lib.timing_wrapper
    def restore_namespaces(self, clusterName, namespacesToRestore="*"):
        namespace = []
        for namespace in self.get_s3_namespaces(clusterName):
            if namespacesToRestore != "*" and namespace not in namespacesToRestore:
                self.log.info("skipping namespace: %s", namespace)
                continue

            self.log.info("restoring namespace: %s", namespace)
            self.strategy.start_namespace(namespace)

            try:
                for kind in Restore.kind_order:
                    prefix = "{}/{}/{}".format(clusterName, namespace, kind)

                    for key, data in self.get_bucket_items(prefix):
                        _, _, _, name = S3.parse_key(key)
                        if Restore.exclude_check(namespace, kind, name):
                            self.log.info("skipping: %s/%s in namespace %s", kind, name, namespace)
                            continue

                        self.log.info("processing %s", key)
                        self.log.debug("%s", data.decode("utf-8"))
                        self.strategy.process_resource(data)
            except ApiException as err:
                if err.status == 409:
                    self.log.warn("resource already exists, skipping")
                else:
                    raise
            self.strategy.finish_namespace()
