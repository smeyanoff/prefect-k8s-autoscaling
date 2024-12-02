#####################################################

install: 
	helm install spark-operator \
		-f values.yaml spark-operator/spark-operator \
		-n spark --create-namespace

upgrade:
	helm upgrade spark-operator \
		-f values.yaml spark-operator/spark-operator \
		-n spark

delete:
	helm uninstall spark-operator \
		-n spark --no-hooks
