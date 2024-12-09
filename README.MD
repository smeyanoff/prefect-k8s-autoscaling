# DESCRIPTION

В этом репозитории представлены примеры развертывания `prefect` в `kubernetes`. 
Данный проект тестировался в кластере `Managed Service For Kubernetes` в `Yandex Cloud`.

Можно выделить следующие преимущества развертывания `prefect` в `kubernetes`:
- Собственное окружение для отдельного DAG (deployment) со своими библиотеками и версией python;
- Возможность динамически выделять ресурсы;

Особенностью шаблонов, преставленных в директории `./templates` является максимальная автоматизация через `GitLab-CI`. 
Джобы автоматически собирают линтят код, собирают контейнер и пушат по api `prefect` при инициализации `Merge Request`. При этом, основная информация о `deployment` (имя, work_pool, regestry и т.д.) объявляется в ci/cd процессе.

# Начало работы

Перед началом работы, вам необходим `prefect-server`, развернутый через helm. 
Все helm репозитории находятся в директории `./helm`.

В директории `./pkg/` находятся библиотеки, необходимые для взаимодействия с `kubernetes`. 
В нашем пайплайне, они вынесены в отдельный `regestry`.
