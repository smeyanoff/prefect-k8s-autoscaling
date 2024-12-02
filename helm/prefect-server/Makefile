#####################################################

.apply-configmap:
	kubectl apply -f configmap.yaml

.delete-configmap:
	kubectl delete -f configmap.yaml


install: .apply-configmap
	helm install prefect-server \
		-f values.yaml prefect/prefect-server \
		-n prefect

upgrade: .apply-configmap
	helm upgrade prefect-server \
		-f values.yaml prefect/prefect-server \
		-n prefect

delete: .delete-configmap
	helm uninstall prefect-server \
		-n prefect
