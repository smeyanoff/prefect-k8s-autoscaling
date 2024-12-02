"""
Модуль для утилит использующихся во flow
"""

import logging

from kubeutils.api import KubeApiV1
from kubeutils.kube import KubeutilsV1
from kubeutils.watch import KubeWatch

# initialization
# инициализируется в отдельном файле из-за особенностей \
# проверки наличия модулей во flow в prefect
logger = logging.Logger(__name__)
kutils = KubeutilsV1.new(
    logger=logger,
    api=KubeApiV1(),
    watch=KubeWatch(),
)
