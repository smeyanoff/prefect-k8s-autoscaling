"""
Based flow file
"""

import os
from prefect import flow, get_run_logger, task

import src.config as config
from src.utils import (
    generate_task_name,
    get_object_name,
    extract_postfix_from_apllication_script_name,
    make_application_name_k8s_compatible,
    kutils,
    s3_client,
    spark_app,
)


@task(task_run_name=generate_task_name)
def upload_script_to_s3(
    application_script_name: str,
) -> None:
    """
    Загружает скрипт в yandex object storage

    application_name:str - имя скрипта в src/application/
    """
    script_path = f"{config.SPARK_APP_PATH}/{application_script_name}"
    object_name = get_object_name(application_script_name)

    s3_client.upload_file(
        script_path,
        os.getenv("S3_BUCKET_NAME"),
        f"spark/scripts/{object_name}",
    )


@task
def create_spark_application(
    application_script_name: str,
    application_namespace: str,
    application_manifest_name: str | None,
    based_manifest_name: str | None,
    application_name: str,
) -> None:
    """
    Creates and deploys a Spark application on Kubernetes using the specified application
    script and configuration details. Downloads necessary secrets and configures the Spark
    application manifest, including environment variables and Hadoop configurations for S3
    access. Supports using custom or default manifests and sets up the application namespace
    and name.

    Args:
        application_script_name (str): The name of the application script.
        application_namespace (str): The Kubernetes namespace for the application.
        application_manifest_name (str | None): The name of the custom application manifest.
        based_manifest_name (str | None): The name of the base manifest for merging.
        application_name (str): The name of the Spark application.
        env_vars (list[dict[str, str]]): A list of environment variables for the application.

    Returns:
        None
    """
    object_name = get_object_name(application_script_name)
    app = spark_app

    if application_manifest_name:
        kutils.logger.info("Use custom manifest.")
        if based_manifest_name:
            app.merge_and_update_manifest(
                f"{config.SPARK_APP_CONFIG_PATH}/{application_manifest_name}",
                f"{config.SPARK_APP_CONFIG_PATH}/{based_manifest_name}",
            )
        app.download_manifest(
            f"{config.SPARK_APP_CONFIG_PATH}/{application_manifest_name}",
        )
    else:
        kutils.logger.info("Use default manifest.")
        app = spark_app.default()
    app.define_script_path(f"s3a://spark/scripts/{object_name}")
    app.define_hadoop_manifest(
        {
            "fs.s3a.access.key": f'{os.getenv("S3_ACCESS_KEY")}',
            "fs.s3a.secret.key": f'{os.getenv("S3_SECRET_KEY")}',
            "fs.s3a.endpoint": f'{os.getenv("S3_ENDPOINT_URL")}/{os.getenv("S3_BUCKET_NAME")}',
            "fs.s3a.connection.ssl.enabled": "true",
            "fs.s3a.path.style.access": "true",
        },
    )
    app.define_app_name(application_name)
    app.define_app_name(application_name)
    app.define_namespace(application_namespace)
    # Env vars here
    app.define_container_env_from(
        config.SPARK_APP_ENV_FROM_VARS,
    )
    app.define_container_env(
        [
            *config.SPARK_APP_ENV_VARS,
            {
                "name": "DATE",
                "value": config.CURRENT_MSK_DATE,
            },
            {
                "name": "NUM_EXECUTORS",
                "value": str(app.get_executor_num),
            },
        ],
    )

    kutils.create_namespaced_custom_object(
        group="sparkoperator.k8s.io",
        version="v1beta2",
        namespace=application_namespace,
        plural="sparkapplications",
        application=app,
    )


@task
def monitor_spark_application(
    application_namespace: str,
    application_name: str,
    running_timeout_s: int,
    pending_timeout_s: int,
) -> None:
    """
    Monitors a Spark application running on Kubernetes by streaming its pod logs.

    This task retrieves the pod name of the Spark application using the specified
    namespace and application name, then continuously streams the pod logs while
    the application is running. It also handles timeouts for both running and
    pending states.

    Args:
        application_namespace (str): \
            The Kubernetes namespace where the Spark application is deployed.
        application_name (str): The name of the Spark application.
        running_timeout_s (int): \
            The timeout in seconds for the application to be in a running state.
        pending_timeout_s (int): \
            The timeout in seconds for the application to be in a pending state.
    """
    selector = "spark-role=driver,sparkoperator.k8s.io/app-name"
    label_selector = f"{selector}={application_name}"

    pod_name = kutils.get_pod_name(
        namespace=application_namespace,
        label_selector=label_selector,
    )

    for log in kutils.while_running(
        func=kutils.stream_pod_log,
        pending_timeout_s=pending_timeout_s,
        pod_name=pod_name,
        namespace=application_namespace,
        timeout_s=running_timeout_s,
    ):
        if any(exceptions in log for exceptions in config.LOG_LEVELS):
            print(log)


@task(
    persist_result=True,
    result_storage=config.S3_BLOCK,
    result_storage_key=(
        "{flow_run.flow_name}/{flow_run.name}/"
        "{parameters[application_script_name]}.json"
    ),
    task_run_name=generate_task_name,
)
def create_and_monitor_spark_application(
    application_script_name: str,
    application_namespace: str,
    application_manifest_name: str | None,
    based_manifest_name: str | None,
    running_timeout_s: int,
    pending_timeout_s: int,
) -> str:
    """
    Creates and monitors a Spark application on Kubernetes.

    This task combines the creation and monitoring of a Spark application by
    utilizing specified script and configuration details. It generates a
    Kubernetes-compatible application name, appends necessary environment
    variables, and manages task execution names. The results are persisted
    to an S3 bucket.

    Args:
        application_script_name (str): The name of the application script.
        application_namespace (str): The Kubernetes namespace for the application.
        application_manifest_name (str | None): The name of the custom application manifest.
        based_manifest_name (str | None): The name of the base manifest for merging.
        running_timeout_s (int): Timeout in seconds for the application to be in a running state.
        pending_timeout_s (int): Timeout in seconds for the application to be in a pending state.
        env_vars (list[dict[str, str]]): A list of environment variables for the application.

    Returns:
        str: A success message indicating the task completion.
    """
    env_vars = config.SPARK_APP_ENV_VARS
    postfix = extract_postfix_from_apllication_script_name(
        application_script_name,
        config.SPARK_APP_SCRIPT_NAME_BODY,
    )
    app_specific_name = config.SPARK_APP_NAME_K8S
    if postfix:
        app_specific_name = f"{config.SPARK_APP_NAME_K8S}-{postfix}"
    logger_name = app_specific_name.title().replace("-", "")  # To Camel Case
    env_vars.append(
        {"name": "LOGGER_NAME", "value": logger_name},
    )
    task_name_addition = f"_{postfix}" if postfix else ""
    application_name_valid = make_application_name_k8s_compatible(
        base_name=config.SPARK_APP_BASED_NAME,
        app_name=app_specific_name,
        name_to_hash=config.CURRENT_MSK_TIMESTAMP,
    )
    create_spark_application.with_options(
        task_run_name=f"create_spark_application{task_name_addition}",
    )(
        application_script_name,
        application_namespace,
        application_manifest_name,
        based_manifest_name,
        application_name_valid,
    )
    monitor_spark_application.with_options(
        task_run_name=f"monitor_spark_application{task_name_addition}",
    )(
        application_namespace,
        application_name_valid,
        running_timeout_s,
        pending_timeout_s,
    )
    return "Success"  # To persist result


@flow(
    name=config.FLOW_NAME,
    log_prints=True,
)
def spark_kubernetes_flow(
    # Scripts
    application_script_name: str,
    application_namespace: str,
    # Manifests
    based_manifest_name: str | None,
    application_manifest_name: str | None,
    # Additional params
    running_timeout_s: int,
    pending_timeout_s: int,
) -> None:
    """
    Executes a flow to deploy and monitor a Spark application on Kubernetes.

    This flow handles the uploading of the application script to S3, and the
    creation and monitoring of the Spark application using Kubernetes. It
    configures environment variables and manages the flow execution with
    logging enabled.

    Args:
        application_script_name (str): The name of the application script.
        application_namespace (str): The Kubernetes namespace for the application.
        based_manifest_name (str | None): The name of the base manifest for merging.
        application_manifest_name (str | None): The name of the custom application manifest.
        running_timeout_s (int): Timeout in seconds for the application to be in a running state.
        pending_timeout_s (int): Timeout in seconds for the application to be in a pending state.
    """
    kutils.logger = get_run_logger()
    upload_script_to_s3(application_script_name)
    create_and_monitor_spark_application(
        application_script_name=application_script_name,
        application_manifest_name=application_manifest_name,
        based_manifest_name=based_manifest_name,
        application_namespace=application_namespace,
        running_timeout_s=running_timeout_s,
        pending_timeout_s=pending_timeout_s,
    )
