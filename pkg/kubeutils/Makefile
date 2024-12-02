PROJECT = kubeutils/
TEST_DIR = tests/
POETRY_VERSION = 1.8.2

# SETUP ########################################################

.install-poetry:
	pip install -U poetry==$(POETRY_VERSION)
	poetry config virtualenvs.in-project true

.install-depends: .install-poetry
	poetry install --sync --no-root

.pre-commit:
	poetry run pre-commit install
	poetry run pre-commit autoupdate

setup: .install-depends .pre-commit

# TESTS ########################################################

testing:
	poetry run python -m unittest discover -s $(TEST_DIR) -v

# LINT #########################################################

lint:
	poetry run ruff check $(PROJECT)

format:
	poetry run ruff format $(PROJECT)
	poetry run ruff check $(PROJECT) --fix

# SUBMIT #######################################################

submit:
	git add .
	git commit -m "$(shell poetry version | grep -Eo '[0-9]+\.[0-9]+\.[0-9]+')"
	git push

# POETRY #######################################################

# открывает терминал c виртуальным окружением этого проекта
shell:
	poetry shell

# обновляет библиотеки
update:
	poetry update

# проверяет соответсвие .lock и .toml файлов
check:
	poetry check --lock
	poetry lock
