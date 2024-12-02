import os
import unittest
import yaml
import tempfile
import shutil


from kubeutils.application import MANIFEST_NOT_FOUND, SparkApplicationV1


class SparkApplicationV1GetExecutorNum(unittest.TestCase):
    def test_get_executor_num_invalid_cfg(self):
        dirpath = tempfile.mkdtemp()
        manifest_path = os.path.join(dirpath, "manifest.yaml")

        # No spec at all
        spark_config = {
            "metadata": {},
        }
        with open(manifest_path, "w") as file:
            yaml.dump(spark_config, file, default_flow_style=False)

        app = SparkApplicationV1()
        app.download_manifest(manifest_path)

        with self.assertRaises(ValueError):
            app.get_executor_num

        # There's spec but nowhere executor params are specified
        spark_config = {
            "spec": {"type": "Python"},
        }
        with open(manifest_path, "w") as file:
            yaml.dump(spark_config, file, default_flow_style=False)

        app = SparkApplicationV1()
        app.download_manifest(manifest_path)

        with self.assertRaises(ValueError):
            app.get_executor_num

    def test_get_executor_num_executor_specified(self):
        dirpath = tempfile.mkdtemp()
        manifest_path = os.path.join(dirpath, "manifest.yaml")

        num_instances = 2

        spark_config = {
            "spec": {"executor": {"instances": num_instances}},
        }
        with open(manifest_path, "w") as file:
            yaml.dump(spark_config, file, default_flow_style=False)

        app = SparkApplicationV1()
        app.download_manifest(manifest_path)

        self.assertEqual(app.get_executor_num, num_instances)

    def test_get_executor_num_dynamic_setup_specified(self):
        dirpath = tempfile.mkdtemp()
        manifest_path = os.path.join(dirpath, "manifest.yaml")

        num_instances = 2
        num_instances_str = str(num_instances)

        spark_config = {
            "spec": {
                "sparkConf": {
                    "spark.dynamicAllocation.enabled": "true",
                    "spark.dynamicAllocation.initialExecutors": "1",
                    "spark.dynamicAllocation.minExecutors": "1",
                    "spark.dynamicAllocation.maxExecutors": num_instances_str,
                },
            },
        }

        with open(manifest_path, "w") as file:
            yaml.dump(spark_config, file, default_flow_style=False)

        app = SparkApplicationV1()
        app.download_manifest(manifest_path)

        self.assertEqual(app.get_executor_num, num_instances_str)

    def test_get_executor_num_both_exec_and_dynamic_setup_specified(self):
        dirpath = tempfile.mkdtemp()
        manifest_path = os.path.join(dirpath, "manifest.yaml")

        num_instances = 2
        num_instances_str = str(num_instances)

        spark_config = {
            "spec": {
                "sparkConf": {
                    "spark.dynamicAllocation.enabled": "true",
                    "spark.dynamicAllocation.initialExecutors": "1",
                    "spark.dynamicAllocation.minExecutors": "1",
                    "spark.dynamicAllocation.maxExecutors": num_instances_str,
                },
                "executor": {"instances": num_instances + 1},  # Other value
            },
        }

        with open(manifest_path, "w") as file:
            yaml.dump(spark_config, file, default_flow_style=False)

        app = SparkApplicationV1()
        app.download_manifest(manifest_path)

        self.assertEqual(app.get_executor_num, num_instances_str)


class TestSparkApplicationV1(unittest.TestCase):
    # Instantiating SparkApplicationV1 and calling default method should download the manifest correctly
    def test_default_method_downloads_manifest(self):
        # Create a dummy manifest file for testing
        dirpath = tempfile.mkdtemp()
        manifest_path = os.path.join(dirpath, "manifest.yaml")

        spark_config = {"spec": {}, "metadata": {}}
        with open(manifest_path, "w") as file:
            yaml.dump(spark_config, file, default_flow_style=False)

        app = SparkApplicationV1()
        app.download_manifest(manifest_path)

        self.assertIsNotNone(app.manifest)
        self.assertIn("spec", app.manifest)
        self.assertIn("metadata", app.manifest)

        shutil.rmtree(dirpath)

    # Calling __call__ method without downloading the manifest should raise TimeoutError
    def test_call_without_manifest_raises_timeout_error(self):
        from kubeutils.application import SparkApplicationV1

        app = SparkApplicationV1()
        with self.assertRaises(TimeoutError):
            app()

        # The method initializes a SparkApplicationV1 instance

    def test_initializes_spark_application_v1_instance(self):
        application = SparkApplicationV1.default()

        self.assertIsInstance(application, SparkApplicationV1)

    def test_set_env_with_manifest(self):
        application = SparkApplicationV1.default()

        self.assertIsInstance(application, SparkApplicationV1)
        # define_container_env sets env for driver and executor containers when manifest is present

        env_vars = [{"name": "NUM_EXECUTORS", "value": "2"}]
        application.define_container_env(env_vars)
        self.assertEqual(application.manifest["spec"]["driver"]["env"], env_vars)
        self.assertEqual(application.manifest["spec"]["executor"]["env"], env_vars)

    def test_set_env_from_with_manifest(self):
        application = SparkApplicationV1.default()

        self.assertIsInstance(application, SparkApplicationV1)
        # define_container_env_from sets envFrom for driver and executor containers when manifest is present

        secrets = [{"secretName": {"key": "value"}}]
        application.define_container_env_from(secrets)
        self.assertEqual(application.manifest["spec"]["driver"]["envFrom"], secrets)
        self.assertEqual(application.manifest["spec"]["executor"]["envFrom"], secrets)

        # define_app_name sets the name in manifest metadata when manifest is present

    # define_container_volumes sets volumes in manifest when manifest is present
    def test_define_container_volumes_sets_volumes(self):
        class MockSparkApplicationV1:
            def __init__(self):
                self.manifest = {"spec": {}}

            def define_container_volumes(
                self,
                volumes: list[dict[str, str | dict[str, str]]],
            ) -> None:
                if not self.manifest:
                    raise TimeoutError(MANIFEST_NOT_FOUND)
                self.manifest["spec"]["volumes"] = volumes

        app = MockSparkApplicationV1()
        volumes = [{"name": "name1", "secret": {"secretName": "name2"}}]
        app.define_container_volumes(volumes)
        assert app.manifest["spec"]["volumes"] == volumes

    # Successfully sets volume mounts for both driver and executor containers when manifest is present
    def test_successful_volume_mounts_set(self):
        class MockSparkApplicationV1:
            def __init__(self):
                self.manifest = {
                    "spec": {
                        "driver": {},
                        "executor": {},
                    },
                }

            def define_container_volume_mounts(
                self,
                volume_mounts: list[dict[str, str | bool]],
            ) -> None:
                if not self.manifest:
                    raise TimeoutError(MANIFEST_NOT_FOUND)
                for container in ("driver", "executor"):
                    self.manifest["spec"][container]["volumeMounts"] = volume_mounts

        app = MockSparkApplicationV1()
        volume_mounts = [
            {
                "name": "test-volume",
                "mountPath": "/mnt/test",
                "readOnly": True,
            },
        ]
        app.define_container_volume_mounts(volume_mounts)

        assert app.manifest["spec"]["driver"]["volumeMounts"] == volume_mounts
        assert app.manifest["spec"]["executor"]["volumeMounts"] == volume_mounts

    def test_merge_and_update_manifest(
        self,
    ):
        app_manifest_name = "app_manifest.yaml"
        based_manifest_name = "base_manifest.yaml"

        app_manifest = {
            "spec": {"driver": {"ex": 3, "mem": 5}},
        }
        based_manifest = {
            "spec": {"driver": {"ex": 1, "name": "a"}},
        }

        expected_merged_manifest = {
            "spec": {"driver": {"ex": 3, "mem": 5, "name": "a"}},
        }

        encoding = "utf-8"

        manifests = [app_manifest, based_manifest]

        manifest_names = [app_manifest_name, based_manifest_name]
        dirpath = tempfile.mkdtemp()
        manifest_paths = [
            f"{dirpath}/{manifest_path}" for manifest_path in manifest_names
        ]
        app_manifest_path, based_manifest_path = manifest_paths

        for manifest_path, manifest in zip(manifest_paths, manifests):
            with open(manifest_path, "w", encoding="utf-8") as fh:
                yaml.dump(manifest, fh)

        application = SparkApplicationV1()

        # Call the method to test
        application.merge_and_update_manifest(
            app_manifest_path,
            based_manifest_path,
            encoding,
        )

        # Assert result
        with open(app_manifest_path, encoding=encoding) as fh:
            resulted_manifest = yaml.load(fh, Loader=yaml.FullLoader)

        assert expected_merged_manifest == resulted_manifest

        shutil.rmtree(dirpath)
