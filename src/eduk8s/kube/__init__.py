import os

from kubernetes.config import new_client_from_config
from kubernetes.config.incluster_config import load_incluster_config
from kubernetes.client.api_client import ApiClient

from openshift.dynamic import DynamicClient

kubernetes_service_host = os.environ.get("KUBERNETES_SERVICE_HOST")
kubernetes_service_port = os.environ.get("KUBERNETES_SERVICE_PORT")


def client():
    if kubernetes_service_host and kubernetes_service_port:
        load_incluster_config()
        k8s_client = ApiClient()
        dyn_client = DynamicClient(k8s_client)
    else:
        k8s_client = new_client_from_config()
        dyn_client = DynamicClient(k8s_client)

    return dyn_client
