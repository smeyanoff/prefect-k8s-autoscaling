"""
Utils for flow run
"""

import logging
import hashlib
import os

import boto3
from kubeutils.api import KubeApiV1
from kubeutils.kube import KubeutilsV1
from prefect.runtime import task_run
from kubeutils.application import SparkApplicationV1

import src.config as config


# initialization
logger = logging.Logger(__name__)
kutils = KubeutilsV1.new(
    logger=logger,
    api=KubeApiV1(),
)
# download secrets to env
kutils.download_secrets(config.KUBE_SECRETS, to_env=True)

# initialize all other secondary flow dependences
s3_client = boto3.client(
    "s3",
    endpoint_url=os.getenv("S3_ENDPOINT_URL"),
    aws_access_key_id=os.getenv("S3_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("S3_SECRET_KEY"),
)

spark_app = SparkApplicationV1()


def make_application_name_k8s_compatible(
    base_name: str,
    app_name: str | None,
    name_to_hash: str,
    max_allowed_length: int = 63,
    ui_postfix_len: int = 7,
    hash_len: int = 6,
) -> str:
    """
    Generate a Kubernetes-compatible application name for spark application.

    Truncate the base name if needed and add a hash suffix and optional app name postfix.

    Args:
        base_name: The base name of the application.
        app_name: The optional app name to include.
        name_to_hash: The string used for generating the hash suffix.
        max_allowed_length: The maximum allowed length for the final name. Defaults to 63.
        ui_postfix_len: The length of the UI postfix. Defaults to 7.
        hash_len: The length of the hash suffix. Defaults to 6.

    Returns:
        str: The Kubernetes-compatible application name.
    """
    hash_suffix = hashlib.md5(name_to_hash.encode()).hexdigest()[:hash_len]
    app_name_contribution = len(app_name) + 1 if app_name else 0
    hash_suffix_contribution = len(hash_suffix) + 1
    truncated_base_name = base_name[
        : min(
            max_allowed_length
            - ui_postfix_len
            - hash_suffix_contribution
            - app_name_contribution,
            len(base_name),
        )
    ]
    app_name_postfix = f"-{app_name}" if app_name else ""
    truncated_name = f"{truncated_base_name}-{hash_suffix}{app_name_postfix}"
    return truncated_name


def extract_postfix_from_apllication_script_name(
    application_script_name: str,
    body_name_convention: str,
) -> str | None:
    """
    Extracts the postfix from an application script name based on a given body name convention.

    Args:
        application_script_name: The name of the application script.
        body_name_convention: The body name convention used to split the script name.

    Returns:
        str | None: The valid postfix extracted from the script name, or None if not found.
    """
    name_ext_rm = application_script_name.split(".")[0]
    first, second = name_ext_rm.split(body_name_convention)
    if first:
        raise RuntimeError("You broke name convention for scripts. Fix it at first.")
    valid_postfix = second[1:] if second else None
    return valid_postfix


def get_object_name(application_script_name: str) -> str:
    """
    Generates an object name for a given application script by extracting its postfix
    and combining it with deployment and configuration details.

    Args:
        application_script_name: The name of the application script.

    Returns:
        str: The constructed object name, including the work pool name, deployment name,
        and the script name with its postfix and extension.
    """
    postfix = extract_postfix_from_apllication_script_name(
        application_script_name,
        config.SPARK_APP_SCRIPT_NAME_BODY,
    )
    script_body_name = f"{config.DEPLOYMENT_TAG}"  # Script version
    script_extension = application_script_name.split(".")[-1]
    if postfix:
        script_body_name = f"{script_body_name}-{postfix}"
    full_script_name = f"{script_body_name}.{script_extension}"
    object_name = (
        f"{config.PREFECT_WORK_POOL_NAME}/{config.DEPLOYMENT_NAME}/{full_script_name}"
    )
    return object_name


def generate_task_name() -> str:
    """
    Generate a Kubernetes-compatible application name for a Spark application.

    This function truncates the base name if necessary and appends a hash suffix
    and an optional application name postfix to ensure the final name adheres to
    Kubernetes naming conventions.

    Args:
        base_name: The base name of the application.
        app_name: An optional application name to include in the final name.
        name_to_hash: The string used to generate the hash suffix.
        max_allowed_length: The maximum length allowed for the final name. Defaults to 63.
        ui_postfix_len: The length of the UI postfix. Defaults to 7.
        hash_len: The length of the hash suffix. Defaults to 6.

    Returns:
        str: A Kubernetes-compatible application name.
    """
    task_name = task_run.task_name

    parameters = task_run.parameters
    postfix = extract_postfix_from_apllication_script_name(
        parameters["application_script_name"],
        config.SPARK_APP_SCRIPT_NAME_BODY,
    )
    if postfix:
        task_name = f"{task_name}_{postfix}"
    return task_name
