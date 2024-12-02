"""
main python flow
"""

import os

from prefect import task, flow, get_run_logger

import src.config as cfg
from src.utils import kutils


@task
def download_secrets():
    """
    Task to download secrets using KubeutilsV1 and set them as environment variables.

    This function retrieves secrets defined in the configuration file and
    prints them. It also prints the value of the "HOST" environment variable
    after setting it from the downloaded secrets.

    Returns:
        None
    """
    secrets = kutils.download_secrets(cfg.KUBE_SECRETS, to_env=True)
    print(secrets)
    print(os.getenv("HOST"))


@task
def read_sql_script(path: str) -> None:
    """
    Reads and prints the contents of a SQL script file.

    Args:
        path (str): The file path to the SQL script.
    """
    with open(path, "r", encoding="utf-8") as f:
        print(f.read())


@flow(
    name=cfg.FLOW_NAME,
    log_prints=True,
)
def python_prefect_flow() -> None:
    """
    Executes the main Prefect flow for processing SQL scripts and managing Kubernetes secrets.

    This flow reads a SQL script from a specified path, downloads Kubernetes secrets
    to environment variables, and logs the process. It utilizes Prefect's flow and task
    decorators for orchestration and logging.

    Returns:
        None
    """
    kutils.logger = get_run_logger()

    read_sql_script("./scripts/test_script.sql")
    download_secrets()

    print("All done")
