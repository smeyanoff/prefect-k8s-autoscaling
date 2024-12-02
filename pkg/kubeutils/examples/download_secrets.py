from logging import Logger
import os

from kubeutils.kube import KubeutilsV1
from kubeutils.api import KubeApiV1
from kubeutils.watch import KubeWatch


log = Logger("download_secrets", level="INFO")
kutils = KubeutilsV1.new(log, KubeApiV1(), KubeWatch())

secrets_dict = {
    "prefect": {
        "s3-secret": [
            "S3_ENDPOINT_URL",
            "S3_ACCESS_KEY",
            "S3_SECRET_KEY",
            "S3_BUCKET_NAME",
        ],
    },
}

# download just one secret
print(
    kutils.download_secret(
        secret_name="s3-secret",
        secret_key="S3_ENDPOINT_URL",
        to_env=True,
    ),
)
# if `to_env` is True -- u can use env_variable reached by 'secret key'
print(os.getenv("S3_ENDPOINT_URL"))
# use download_secrets method with secret dict
print(kutils.download_secrets(secrets_dict))
