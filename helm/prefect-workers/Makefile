#####################################################

install:
	helm install prefect-worker-test  \
		prefect/prefect-worker -f values_test.yaml \
		-n prefect
	helm install prefect-worker-main  \
		prefect/prefect-worker -f values_main.yaml \
		-n prefect

upgrade:
	helm upgrade prefect-worker-test \
		-f values_test.yaml prefect/prefect-worker \
		-n prefect
	helm upgrade prefect-worker-main \
		-f values_main.yaml prefect/prefect-worker \
		-n prefect

delete:
	helm uninstall prefect-worker-test  \
		-n prefect
	helm uninstall prefect-worker-main  \
		-n prefect