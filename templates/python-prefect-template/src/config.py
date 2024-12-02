"""
flow job config
"""

import os
import datetime


# ENV
DEPLOYMENT_NAME = os.getenv("DEPLOYMENT_NAME")
DEPLOYMENT_TAG = os.getenv("DEPLOYMENT_TAG")
PREFECT_WORK_POOL_NAME = os.getenv("PREFECT_WORK_POOL_NAME")
FLOW_NAME = f"{DEPLOYMENT_NAME}-{PREFECT_WORK_POOL_NAME}"

# TIME
CURRENT_MSK_DT = datetime.datetime.now() + datetime.timedelta(hours=3)
CURRENT_MSK_TIMESTAMP = CURRENT_MSK_DT.strftime("%m-%d-%Y-%H-%M-%S")
CURRENT_MSK_DATE = CURRENT_MSK_DT.strftime("%Y-%m-%d")


# OTHER
LOG_LEVEL = "INFO"  # INFO | WARNING | ERROR
## kubernetes secrets uploaded to prefect job environment
KUBE_SECRETS = {
    "prefect": {
        "clickhouse-ta-etl-user-secret": [
            "HOST",
        ],
    },
}
