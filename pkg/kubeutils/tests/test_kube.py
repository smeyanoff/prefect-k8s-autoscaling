import os
import base64
from logging import Logger

import unittest
from unittest.mock import Mock
import unittest.mock

from kubeutils.api import ApiInterface
from kubeutils.kube import KubeutilsV1


class TestKubeutils(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_logger = Mock(spec=Logger)
        self.mock_api = Mock(spec=ApiInterface)

        self.kubeutils_instance = KubeutilsV1.new(
            self.mock_logger,
            self.mock_api,
        )
        self.kubeutils_instance.config = True

    # Creating a new instance of Kubeutils with valid logger, API, and Watch interfaces
    def test_create_new_instance(self):
        self.assertIsInstance(self.kubeutils_instance, KubeutilsV1)
        self.assertIs(self.kubeutils_instance.logger, self.mock_logger)
        self.assertIs(self.kubeutils_instance.api, self.mock_api)

    def test_download_multiple_secrets_async(self):
        self.mock_api.read_namespaced_secret.side_effect = [
            Mock(data={"key1": base64.b64encode(b"value1").decode("utf-8")}),
            Mock(data={"key2": base64.b64encode(b"value2").decode("utf-8")}),
        ]
        secret_dict = {
            "namespace1": {
                "secret1": ["key1"],
                "secret2": ["key2"],
            },
        }
        result_async = self.kubeutils_instance.download_secrets(
            secret_dict,
            to_env=True,
        )
        expected = [
            ["namespace1", "key1", "value1"],
            ["namespace1", "key2", "value2"],
        ]
        self.assertEqual(result_async, expected)
        self.assertEqual("value1", os.getenv("key1"))

    def test_download_multiple_secrets_sync(self):
        self.mock_api.read_namespaced_secret.side_effect = [
            Mock(data={"key1": base64.b64encode(b"value1").decode("utf-8")}),
            Mock(data={"key2": base64.b64encode(b"value2").decode("utf-8")}),
        ]
        secret_dict = {
            "namespace1": {
                "secret1": ["key1"],
                "secret2": ["key2"],
            },
        }
        result_sync = self.kubeutils_instance.download_secrets(
            secret_dict,
            to_env=True,
            materialize=True,
        )
        expected = [
            ["namespace1", "key1", "value1"],
            ["namespace1", "key2", "value2"],
        ]
        self.assertEqual(result_sync, expected)
        self.assertEqual("value1", os.getenv("key1"))

    # Handles empty secret_dict gracefully
    def test_empty_secret_dict(self):
        secret_dict = {}
        result = self.kubeutils_instance.download_secrets(secret_dict)
        assert result == []
