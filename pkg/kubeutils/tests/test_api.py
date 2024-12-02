import unittest
from unittest.mock import patch, Mock

from kubernetes.client import V1Secret, V1Pod, V1PodList

from kubeutils.api import KubeApiV1
from kubeutils.application import ApplicationInterface


class TestKubeApiV1(unittest.TestCase):
    def setUp(self) -> None:
        self.api = KubeApiV1()

    @patch.object(KubeApiV1, "read_namespaced_secret")
    def test_read_namespaced_secret(self, mocked_secret):
        mocked_secret.return_value = V1Secret()

        result = self.api.read_namespaced_secret(name="my-secret", namespace="default")

        mocked_secret.assert_called_once()

        assert isinstance(result, V1Secret)

    @patch.object(KubeApiV1, "read_namespaced_pod")
    def test_read_namespaced_pod(self, mocked_secret):
        mocked_secret.return_value = V1Pod()

        result = self.api.read_namespaced_pod(name="my-pod", namespace="default")

        mocked_secret.assert_called_once()

        assert isinstance(result, V1Pod)

    @patch.object(KubeApiV1, "list_namespaced_pod")
    def test_list_namespaced_pod(self, mocked_secret):
        mocked_secret.return_value = V1PodList(items=[1, 2, 3])

        result = self.api.list_namespaced_pod(
            namespace="my-pod",
            label_selector="selector",
        )

        mocked_secret.assert_called_once()

        assert isinstance(result, V1PodList)

    @patch.object(KubeApiV1, "read_namespaced_pod_log")
    def test_read_namespaced_pod_log(self, mocked_secret):
        mocked_secret.return_value = "pod logs"

        result = self.api.read_namespaced_pod_log(name="my-pod", namespace="default")

        mocked_secret.assert_called_once()

        assert isinstance(result, str)

    # Successfully create a custom object in the specified namespace
    @patch.object(KubeApiV1, "create_namespaced_custom_object", return_value={})
    def test_create_custom_object_success(self, mocker):
        application = Mock(spec=ApplicationInterface)
        application.return_value = {}

        result = self.api.create_namespaced_custom_object(
            group="example.com",
            version="v1",
            namespace="default",
            plural="examples",
            application=application,
        )

        assert result == {}
        mocker.assert_called_once_with(
            group="example.com",
            version="v1",
            namespace="default",
            plural="examples",
            application=application,
        )

    @patch.object(
        KubeApiV1,
        "list_pod_for_all_namespaces",
        return_value=V1PodList(items=[V1Pod()]),
    )
    def test_list_pod_for_all_namespaces_returns_pods(self, mocker):
        result = self.api.list_pod_for_all_namespaces()

        self.assertIsInstance(result, V1PodList)
        self.assertGreater(len(result.items), 0)
        mocker.assert_called_once_with()
