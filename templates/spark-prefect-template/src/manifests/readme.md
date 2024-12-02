# Spark Manifests

Директория предназначена для манифестов спарка.

По умолчанию будет использоваться `spark_based.yaml` манифест. Для перезаписи конкретных аргументов (например, ресурсов), можно создать отдельный манифест-конфиг и передать его в качестве переменной.

Если нужно создать отличный конфиг от конфига по умолчанию, то можно создать новый и в качестве базового указать `None`.

## Tolerations

Про tolerations и affinity можно прочитать в [документации](https://wiki.yandex.ru/ons-home/servisy/yandex-clo/managed-service-for-kubernetes/affinity-i-tolerations/).
Для высоконагруженных приложений нужно использовать:

```
tolerations:
      - key: role
        operator: Equal
        value: spark-app-hl
        effect: NoSchedule
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
        - matchExpressions:
            - key: role
              operator: In
              values: [spark-app-hl]
```

для "обычных" приложений:

```
nodeAffinity:
        requiredDuringSchedulingIgnoredDuringExecution:
          nodeSelectorTerms:
            - matchExpressions:
                - key: role
                  operator: In
                  values: [spark-app]
```
