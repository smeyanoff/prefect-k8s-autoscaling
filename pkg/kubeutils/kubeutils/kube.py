import base64
import datetime
import os
import threading
import time
from logging import Logger
from typing import Callable, Any, Generator

from kubernetes import config
from kubernetes.client import V1PodList

from kubeutils.api import ApiInterface
from kubeutils.application import ApplicationInterface

# class
CONFIG_WARN = "config is not loaded using on-system default. \
    build class using .new() method"
CLIENT_NOT_INITIALIZED = "client not initialized. \
    build class using .new() method"
# pod's phases
POD_ALLOCATING_TIMEOUT = "pod wasn`t allocated for 3 hours"
POD_RUNNING_TIMEOUT = "pod running timeout"
POD_PENDING_TIMOUT = "pod pending timeout"


class KubeutilsV1:
    """
    A class representing utilities for interacting with Kubernetes resources.

    Attributes:
        logger (Logger): An instance of the Logger class for logging purposes.
        config (bool): A boolean indicating if the Kubernetes configuration is loaded.
        api (ApiInterface | None): An instance of the ApiInterface class for interacting with Kubernetes API.
        watch (Watch | None): An instance of the Watch class for watching Kubernetes resources.

    Methods:
        new(logger: Logger, api: ApiInterface, watch: Watch) -> Kubeutils:
            Creates a new instance of the Kubeutils class with the provided logger, API interface, and Watch interface.

        download_secret(secret_name: str, secret_key: str, namespace: str = "prefect") -> str:
            Downloads a secret from Kubernetes and returns its value.

        download_secrets(secret_dict: dict[str, dict]) -> dict:
            Downloads multiple secrets based on the provided dictionary of secrets.

        get_pod_name(namespace: str, label_selector: str, timeout_s: int = 10800) -> str:
            Retrieves the name of a pod based on the namespace and label selector.

        get_pod_phase(pod_name: str, namespace: str) -> str:
            Retrieves the phase of a pod based on the pod name and namespace.

        stream_pod_log(pod_name: str, namespace: str, timeout_s: int = 3600) -> None:
            Streams the logs of a specified pod in a given namespace for a specified amount of time.

        while_running(func: Callable, pod_name: str, \
            namespace: str, pending_timeout_s: int = 3600, *args, **kwargs) -> None:
            Executes a given function while monitoring the phase of a pod in a Kubernetes cluster.

    Raises:
        TimeoutError: If the streaming of logs exceeds the specified timeout,\
             or if the pending timeout is exceeded while waiting for the pod phase to change.
        LookupError: If the API client is not initialized.
        ChildProcessError: If the pod phase is 'Failed'.

    Returns:
        None
    """

    def __init__(self, logger: Logger) -> None:
        self.logger: Logger = logger
        self.config: bool = False
        self.api: ApiInterface | None = None

    @staticmethod
    def new(
        logger: Logger,
        api: ApiInterface,
    ) -> "KubeutilsV1":
        """
        Creates a new instance of the Kubeutils class with the provided logger, API interface, and Watch interface.

        Args:
            logger (Logger): An instance of the Logger class for logging purposes.
            api (ApiInterface): An instance of the ApiInterface class for interacting with Kubernetes API.
            watch (Watch): An instance of the Watch class for watching Kubernetes resources.

        Returns:
            Kubeutils: A new instance of the Kubeutils class initialized with the provided logger, API interface, and Watch interface.
        """

        kubeclass = KubeutilsV1(logger=logger)
        kubeclass.__load_k8s_config()
        kubeclass.__init_api(api=api)

        return kubeclass

    def __init_api(self, api: ApiInterface) -> None:
        self.api = api

    def __load_k8s_config(self) -> None:
        # download config
        self.logger.info("download k8s config")
        try:
            self.logger.info("running incluster config")
            config.load_incluster_config()
            self.config = True
        except config.ConfigException:
            self.logger.info("running outside of k8s cluster config")
            config.load_kube_config()
            self.config = True

    def download_secret(
        self,
        secret_name: str,
        secret_key: str,
        namespace: str = "prefect",
        to_env: bool = False,
    ) -> str:
        """
        secret_name: str -- имя секрета
        secret_key: str -- ключ значения секрета
        namespace: str default "prefect" -- namespace секрета
        to_env: bool default false -- записывает секрет в переменную окружения

        return: str -- значение секрета
        """

        self.logger.info(f"download secret: {secret_name} {secret_key}")

        if not self.config:
            self.logger.warning(CONFIG_WARN)

        if not self.api:
            raise LookupError(CLIENT_NOT_INITIALIZED)

        # Get secret
        secret = self.api.read_namespaced_secret(
            name=secret_name,
            namespace=namespace,
        )

        secret_data = secret.data[secret_key]

        decoded_secret = base64.b64decode(secret_data).decode("utf-8")

        if to_env:
            os.environ[secret_key] = decoded_secret

        return decoded_secret

    def download_secrets(
        self,
        secret_dict: dict[str, dict[str, list]],
        to_env: bool = False,
        materialize: bool = False,
    ) -> list:
        """
        secret_dict: dict -- словарь вида \n
            {"namespace": {"secret_name": ["secret_key", ...], ...}, ...}
        to_env: bool default false -- записывает секрет в переменную окружения
        materialize: bool default dalse -- возвращает лист с переменными

        return [["namespace", "secret_key", "secret_value"],...]
        """
        if not secret_dict:
            return []

        def synchronized_write(lock, ret_list, func, *args, **kwargs):
            with lock:
                result = func(*args, **kwargs)
                ret_list.append(
                    [kwargs["namespace"], kwargs["secret_key"], result],
                )

        self.logger.info("download secrets...")

        if not self.config:
            self.logger.warning(CONFIG_WARN)

        space = []
        # key, name and namespace secret
        _ = [
            [
                [space.append([n, k, ns]) for k in secret_dict[ns][n]]
                for n in secret_dict[ns].keys()
            ]
            for ns in secret_dict.keys()
        ]

        return_list = []

        if materialize:
            for secret in space:
                return_list.append(
                    [
                        secret[2],  # namespace
                        secret[1],  # key
                        self.download_secret(
                            secret_name=secret[0],
                            secret_key=secret[1],
                            namespace=secret[2],
                            to_env=to_env,
                        ),
                    ],
                )
            return return_list

        lock = threading.Lock()

        # get a space of all variants

        threads = []

        for secret in space:
            thread = threading.Thread(
                target=synchronized_write,
                args=(
                    lock,
                    return_list,
                    self.download_secret,
                ),
                kwargs={
                    "secret_name": secret[0],
                    "secret_key": secret[1],
                    "namespace": secret[2],
                    "to_env": to_env,
                },
            )
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        return return_list

    def get_pod_name(
        self,
        namespace: str,
        label_selector: str,
        timeout_s: int = 10800,
    ) -> str:
        """
        namespace: str -- namespace пода
        label_selectot: str
        timeout: int -- количество секунд для аллокации пода. \
            По истечению поднимает ошибку TimeoutError

        return driver_pod_name: str -- имя пода в кластере
        """

        now = datetime.datetime.now()

        while True:
            time_gone = datetime.datetime.now() - now

            pods = self.api.list_namespaced_pod(
                namespace=namespace,
                label_selector=label_selector,
            ).items
            if pods:
                driver_pod_name = pods[0].metadata.name
                self.logger.info(
                    f"pod was allocated ~ {time_gone.total_seconds()} seconds",
                )
                break
            time.sleep(5)

            if time_gone.total_seconds() > timeout_s:
                raise TimeoutError(POD_ALLOCATING_TIMEOUT)

        return driver_pod_name

    def get_pod_phase(
        self,
        pod_name: str,
        namespace: str,
    ) -> str:
        """
        pod_name: str -- the name of the pod
        namespace: str -- the namespace of the pod

        return: str -- the phase of the pod
        """
        pod = self.api.read_namespaced_pod(
            name=pod_name,
            namespace=namespace,
        )
        phase = pod.status.phase

        return phase

    def stream_pod_log(
        self,
        pod_name: str,
        namespace: str,
        timeout_s: int = 3600,
    ) -> Generator[str, None, None]:
        """
        Generator that streams the logs of a specified pod in a given namespace for a specified amount of time.

        Args:
            pod_name (str): The name of the pod whose logs to stream.
            namespace (str): The namespace of the pod.
            timeout_s (int, optional): The maximum time (in seconds) to stream the logs before raising a TimeoutError. Defaults to 3600.

        Raises:
            TimeoutError: If the streaming of logs exceeds the specified timeout_s.

        Yields:
            str: A line from the pod's logs
        """

        now = datetime.datetime.now()

        response = self.api.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            _preload_content=False,
            follow=True,
            pretty=True,
        )

        for event in response.stream(decode_content=False):
            time_gone = datetime.datetime.now() - now
            if time_gone.total_seconds() > timeout_s:
                raise TimeoutError(POD_RUNNING_TIMEOUT)

            yield event.decode("utf-8")

    def while_running(
        self,
        func: Callable,
        pending_timeout_s: int | None,
        **kwargs: Any,
    ) -> Any:
        """
        Executes a given function while monitoring the phase of a pod in a Kubernetes cluster.

        Args:
            func (Callable): The function to execute.
            pending_timeout_s (int | None): The maximum time to wait for the pod phase to change.
            **kwargs (Any): Additional keyword arguments to pass to the function.
                pod_name (str): pod name
                namespace (str): pod namespace

        Raises:
            TimeoutError: If the pending timeout is exceeded while waiting for the pod phase to change.
            ChildProcessError: If the pod phase is 'Failed'.

        Returns:
            None
        """
        now = datetime.datetime.now()

        self.logger.info(kwargs)

        while True:
            time.sleep(30)

            phase = self.get_pod_phase(kwargs["pod_name"], kwargs["namespace"])

            if phase == "Running":
                self.logger.info("pod is running...")
                return func(**kwargs)
            elif phase == "Failed":
                raise ChildProcessError("something went wrong")
            elif phase == "Pending":
                self.logger.info("pending...")
            else:
                self.logger.info("job has done")
                break
            time_gone = datetime.datetime.now() - now
            if time_gone.total_seconds() > pending_timeout_s:
                raise TimeoutError(f"waiting pod timeout {POD_PENDING_TIMOUT}")

    def create_namespaced_custom_object(
        self,
        group: str,
        version: str,
        namespace: str,
        plural: str,
        application: ApplicationInterface,
    ) -> object:
        self.logger.info("commit application...")
        app = self.api.create_namespaced_custom_object(
            group=group,
            version=version,
            namespace=namespace,
            plural=plural,
            application=application,
        )
        self.logger.info("commited")

        return app

    def get_pods_all_namespaces(
        self,
        **kwargs: Any,
    ) -> V1PodList:
        return self.api.list_pod_for_all_namespaces(**kwargs)

    def delete_pod(
        self,
        name: str,
        namespace: str,
        **kwargs: Any,
    ) -> None:
        self.api.delete_namespaced_pod(
            name=name,
            namespace=namespace,
            **kwargs,
        )
