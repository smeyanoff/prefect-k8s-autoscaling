"""
Project config
"""

import os
import datetime

from prefect_aws.s3 import S3Bucket


# ENV
DEPLOYMENT_NAME = os.getenv("DEPLOYMENT_NAME")
DEPLOYMENT_TAG = os.getenv("DEPLOYMENT_TAG")
PREFECT_WORK_POOL_NAME = os.getenv("PREFECT_WORK_POOL_NAME")
FLOW_NAME = f"{DEPLOYMENT_NAME}-{PREFECT_WORK_POOL_NAME}"

# TIME
CURRENT_MSK_DT = datetime.datetime.now() + datetime.timedelta(hours=3)
CURRENT_MSK_TIMESTAMP = CURRENT_MSK_DT.strftime("%m-%d-%Y-%H-%M-%S")
CURRENT_MSK_DATE = CURRENT_MSK_DT.strftime("%Y-%m-%d")

# SPARK APPLICATION
SPARK_APP_NAME_K8S = "spark-app"
SPARK_APP_SCRIPT_NAME_BODY = "spark_application"
SPARK_APP_BASED_NAME = f"{DEPLOYMENT_NAME}"
SPARK_APP_PATH = "/opt/prefect/src/application"
SPARK_APP_CONFIG_PATH = "/opt/prefect/src/manifests"
## env vars that can be passed directly
SPARK_APP_ENV_VARS = [
    {"name": "FLOW_NAME", "value": FLOW_NAME},
]
## env vars that can be passed through s3 secrets
SPARK_APP_ENV_FROM_VARS = [
    {"secretRef": {"name": "oracle-secret"}},
    {"secretRef": {"name": "s3-secret"}},
]

# OTHER
LOG_LEVELS = ["WARNING", "ERROR"]  # INFO | WARNING | ERROR
## kubernetes secrets uploaded to prefect job environment
KUBE_SECRETS = {
    "prefect": {
        "s3-secret": [
            "S3_ENDPOINT_URL",
            "S3_ACCESS_KEY",
            "S3_SECRET_KEY",
            "S3_BUCKET_NAME",
        ],
    },
}

# S3 Persisting
S3_BLOCK_NAME = "yandex-object-storage"
S3_BLOCK = S3Bucket.load(S3_BLOCK_NAME)
