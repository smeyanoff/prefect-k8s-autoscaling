import importlib.resources as pkg_resources
from collections import OrderedDict
import hiyapyco

import yaml
from interface import Interface, implements

MANIFEST_NOT_FOUND = "download manifest first use .download_manifest()"


class ApplicationInterface(Interface):
    def __call__(self) -> dict:
        "Return the Kubernetes application manifesturation dictionary"

    @staticmethod
    def default() -> "ApplicationInterface":
        """
        Download default manifesturation

        Returns:
            ApplicationInterface: An instance of ApplicationInterface with the default manifesturation
        """

    def download_manifest(
        self,
        manifest_path: str,
        encoding: str = "utf-8",
    ) -> None:
        "Download the YAML manifesturation file"


class SparkApplicationV1(implements(ApplicationInterface)):
    def __init__(self):
        self.manifest = None

    def __call__(self) -> dict:
        if not self.manifest:
            raise TimeoutError(MANIFEST_NOT_FOUND)
        return self.manifest

    @property
    def get_executor_num(self) -> int:
        """Return the maximum possible number of executor instances allowed by config."""
        if cfg_spec := self.manifest.get("spec"):
            if spark_cfg := cfg_spec.get("sparkConf"):
                if exec_num := spark_cfg.get("spark.dynamicAllocation.maxExecutors"):
                    return exec_num
            if exec_cfg := cfg_spec.get("executor"):
                if exec_num := exec_cfg.get("instances"):
                    return exec_num
        raise ValueError("Config is invalid.")

    @staticmethod
    def default() -> "SparkApplicationV1":
        application = SparkApplicationV1()
        with pkg_resources.path("kubeutils.manifests", "sparkV1.yaml") as fpath:
            application.download_manifest(fpath)

        return application

    def download_manifest(
        self,
        manifest_path: str,
        encoding: str = "utf-8",
    ) -> None:
        try:
            # Загрузим манифест SparkApplication
            with open(manifest_path, encoding=encoding) as fh:
                self.manifest = yaml.load(fh, Loader=yaml.FullLoader)
        except IOError as e:
            print(f"error reading file: {e}")

    def merge_and_update_manifest(
        self,
        app_manifest_path: str,
        based_manifest_path: str,
        encoding: str = "utf-8",
    ) -> None:
        """Обновить манифест приложения, используя склейку базового конфига и приложения.

        В случае совпадения аргументов, конфиг приложения перезаписывает аргументы из базового.

        Удобно для мульти Спарк аппликейшн с одинаковым конфигом.
        """
        manifest_updated = hiyapyco.load(
            based_manifest_path,
            app_manifest_path,
            method=hiyapyco.METHOD_MERGE,
            interpolate=True,
            failonmissingfiles=True,
        )
        yaml.add_representer(
            OrderedDict,
            lambda dumper, data: dumper.represent_mapping(
                "tag:yaml.org,2002:map",
                data.items(),
            ),
        )
        with open(app_manifest_path, "w", encoding=encoding) as fh:
            yaml.dump(manifest_updated, fh)

    def define_container_env(
        self,
        env_vars: list[dict[str, str]],
    ) -> None:
        if not self.manifest:
            raise TimeoutError(MANIFEST_NOT_FOUND)
        for container in ("driver", "executor"):
            self.manifest["spec"][container]["env"] = env_vars

    def define_container_env_from(
        self,
        secrets: list[dict[str, dict[str, str]]],
    ) -> None:
        if not self.manifest:
            raise TimeoutError(MANIFEST_NOT_FOUND)
        for container in ("driver", "executor"):
            self.manifest["spec"][container]["envFrom"] = secrets

    def define_container_volumes(
        self,
        volumes: list[dict[str, str | dict[str, str]]],
    ) -> None:
        if not self.manifest:
            raise TimeoutError(MANIFEST_NOT_FOUND)
        self.manifest["spec"]["volumes"] = volumes

    def define_container_volume_mounts(
        self,
        volume_mounts: list[dict[str, str | bool]],
    ) -> None:
        if not self.manifest:
            raise TimeoutError(MANIFEST_NOT_FOUND)
        for container in ("driver", "executor"):
            self.manifest["spec"][container]["volumeMounts"] = volume_mounts

    def define_script_path(
        self,
        script_path: str,
    ) -> None:
        if not self.manifest:
            raise TimeoutError(MANIFEST_NOT_FOUND)
        # Необходимо задать путь до исполняемого спарком скрипта
        self.manifest["spec"]["mainApplicationFile"] = script_path

    def define_hadoop_manifest(
        self,
        manifest: dict[str, str],
    ) -> None:
        if not self.manifest:
            raise TimeoutError(MANIFEST_NOT_FOUND)
        # И соответствующие env для доступа к нему
        self.manifest["spec"]["hadoopConf"] = manifest

    def define_app_name(
        self,
        name: str,
    ) -> None:
        if not self.manifest:
            raise TimeoutError(MANIFEST_NOT_FOUND)
        self.manifest["metadata"]["name"] = name

    def define_namespace(
        self,
        namespace: str,
    ) -> None:
        if not self.manifest:
            raise TimeoutError(MANIFEST_NOT_FOUND)
        self.manifest["metadata"]["namespace"] = namespace
