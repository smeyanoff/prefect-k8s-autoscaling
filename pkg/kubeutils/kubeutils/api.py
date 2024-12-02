"""
General api interface for kubeutils
"""

from interface import Interface, implements
import urllib3
import kubernetes
from kubernetes.client import (
    CoreV1Api,
    CustomObjectsApi,
)

from kubeutils.application import ApplicationInterface


class ApiInterface(Interface):
    def read_namespaced_secret(
        self,
        name: str,
        namespace: str,
        **kwargs,
    ) -> kubernetes.client.V1Secret:
        "read secret from k8s"

    def list_namespaced_pod(
        self,
        namespace: str,
        label_selector: str,
        **kwargs,
    ) -> kubernetes.client.V1PodList:
        "list k8s namespace pod"

    def read_namespaced_pod(
        self,
        name: str,
        namespace: str,
        **kwargs,
    ) -> kubernetes.client.V1Pod:
        "read k8s namespace pod"

    def read_namespaced_pod_log(
        self,
        name: str,
        namespace: str,
        **kwargs,
    ) -> str:
        "read k8s pod log"

    def create_namespaced_custom_object(
        self,
        group: str,
        version: str,
        namespace: str,
        plural: str,
        application: ApplicationInterface,
        **kwargs,
    ) -> object:
        "create k8s object"

    def list_pod_for_all_namespaces(
        self,
        **kwargs,
    ) -> kubernetes.client.V1PodList:
        "get list of all pods"

    def delete_namespaced_pod(
        self,
        name: str,
        namespace: str,
        **kwargs,
    ) -> None:
        "delete pod"


class KubeApiV1(implements(ApiInterface)):
    """
    KubeApi class implementing the ApiInterface interface, providing methods to interact with Kubernetes resources using CoreV1Api and CustomObjectsApi.

    Attributes:
        None

    Methods:
        read_namespaced_secret(name: str, namespace: str) -> kubernetes.client.V1Secret: Read a secret from Kubernetes.
        list_namespaced_pod(namespace: str, label_selector: str) -> kubernetes.client.V1PodList: List pods in a Kubernetes namespace.
        read_namespaced_pod(name: str, namespace: str) -> kubernetes.client.V1Pod: Read a pod in a Kubernetes namespace.
        read_namespaced_pod_log(name: str, namespace: str) -> str: Read logs of a pod in a Kubernetes namespace.
        create_namespaced_custom_object(group: str, version: str, namespace: str, plural: str, application: ApplicationInterface): Create a custom object in a Kubernetes namespace.
    """

    def __init__(self):
        self._core_v1_api = None
        self._custom_objects_api = None

    @property
    def core_v1_api(self):
        if not self._core_v1_api:
            self._core_v1_api = CoreV1Api()
        return self._core_v1_api

    @property
    def custom_objects_api(self):
        if not self._custom_objects_api:
            self._custom_objects_api = CustomObjectsApi()
        return self._custom_objects_api

    def read_namespaced_secret(
        self,
        name: str,
        namespace: str,
        **kwargs,
    ) -> kubernetes.client.V1Secret:
        return self.core_v1_api.read_namespaced_secret(
            name=name,
            namespace=namespace,
            **kwargs,
        )

    def list_namespaced_pod(
        self,
        namespace: str,
        label_selector: str,
        **kwargs,
    ) -> kubernetes.client.V1PodList:
        return self.core_v1_api.list_namespaced_pod(
            namespace=namespace,
            label_selector=label_selector,
            **kwargs,
        )

    def read_namespaced_pod(
        self,
        name: str,
        namespace: str,
        **kwargs,
    ) -> kubernetes.client.V1Pod:
        return self.core_v1_api.read_namespaced_pod(
            name=name,
            namespace=namespace,
            **kwargs,
        )

    def read_namespaced_pod_log(
        self,
        name: str,
        namespace: str,
        **kwargs,
    ) -> str | urllib3.HTTPResponse:
        return self.core_v1_api.read_namespaced_pod_log(
            name=name,
            namespace=namespace,
            **kwargs,
        )

    def create_namespaced_custom_object(
        self,
        group: str,
        version: str,
        namespace: str,
        plural: str,
        application: ApplicationInterface,
        **kwargs,
    ) -> object:
        return self.custom_objects_api.create_namespaced_custom_object(
            group=group,
            version=version,
            namespace=namespace,
            plural=plural,
            body=application(),
            **kwargs,
        )

    def list_pod_for_all_namespaces(
        self,
        **kwargs,
    ) -> kubernetes.client.V1PodList:
        return self.core_v1_api.list_pod_for_all_namespaces(**kwargs)

    def delete_namespaced_pod(
        self,
        name: str,
        namespace: str,
        **kwargs,
    ) -> None:
        self.core_v1_api.delete_namespaced_pod(
            name=name,
            namespace=namespace,
            **kwargs,
        )
