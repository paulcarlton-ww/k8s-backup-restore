import re
import os
import logging
import subprocess
from kubernetes import client, config
import yaml
import tempfile

import utilslib.library as lib

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class RestoreStrategy:
    def __init__(self, cluster_name):
        self.cluster_name = cluster_name

    def start_namespace(self, namespace):
        raise NotImplementedError

    
    def process_resource(self, resource_data):
        raise NotImplementedError

    def finish_namespace(self):
        raise NotImplementedError

class KubectlRestoreStrategy(RestoreStrategy):
    def __init__(self, cluster_name, kubectl_path, temp_folder = tempfile.gettempdir(), dry_run = False):
        super().__init__(cluster_name)
        self.kubectl_path = kubectl_path
        self.temp_folder = temp_folder
        self.dry_run = dry_run

    def start_namespace(self, namespace):
        self._filename = "{}/{}.yaml".format(self.temp_folder,namespace)
        if os.path.exists(self._filename):
            os.remove(self._filename)
        self._output_file = open(self._filename, "w+")
        logger.debug("working file for namespace %s is %s", namespace, self._filename) 

    def process_resource(self, resource_data):
        self._output_file.write(str(resource_data, 'utf-8'))
        self._output_file.write("---\n")

    def finish_namespace(self):
        self._output_file.close()
        
        command = "{} apply -f {}".format(self.kubectl_path, self._filename)
        if self.dry_run:
            command += " --dry-run"
        logger.debug("kubectl command: %s", command)

        logger.info("Applying file %s using kubectl", self._filename)
        p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
        (output, err) = p.communicate()

        status = p.wait()
        logger.info("Kubectl command status/return code: %d", status)
        logger.debug("Kubectl output:\n%s", output)

class SingleResourceApplyStrategy(RestoreStrategy):
    def __init__(self, cluster_name, in_cluster = False) -> None:
        super().__init__(cluster_name)
        if in_cluster:
            config.load_incluster_config()
        else: 
            config.load_kube_config()
        self._client = client.ApiClient()

    def start_namespace(self, namespace):
       self.namespace = namespace

    def process_resource(self, resource_data):
        doc = yaml.load(resource_data, Loader=yaml.FullLoader)

        group, _, version = doc["apiVersion"].partition("/")
        if version == "":
            version = group
            group = "core"

        group = "".join(group.rsplit(".k8s.io", 1))
        group = "".join(word.capitalize() for word in group.split('.'))
        fcn_to_call = "{0}{1}Api".format(group, version.capitalize())
        k8s_api = getattr(client, fcn_to_call)(self._client)

        kind = doc["kind"]
        kind = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', kind)
        kind = re.sub('([a-z0-9])([A-Z])', r'\1_\2', kind).lower()

        if hasattr(k8s_api, "create_namespaced_{0}".format(kind)):
            resp = getattr(k8s_api, "create_namespaced_{0}".format(kind))(
                body=doc, namespace=self.namespace)
        else:
            resp = getattr(k8s_api, "create_{0}".format(kind))(
                body=doc)

        print("{0} created. status='{1}'".format(kind, str(resp.status)))
        

    def finish_namespace(self):
        logger.info("finished processing namespace %s", self.namespace)