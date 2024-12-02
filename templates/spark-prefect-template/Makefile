#################################################################################
# GLOBALS                                                                       #
#################################################################################

PROJECT = src/
POETRY_VERSION = 1.8.3
VENV = .venv
TEST_DIR = tests/

#################################################################################
# COMMANDS                                                                      #
#################################################################################

# SETUP #######################################################

.install-poetry:
	pip install -U poetry==$(POETRY_VERSION) -I
	poetry config virtualenvs.in-project true

.install-depends: .install-poetry
	poetry install --sync --no-root
	# poetry self add poetry-plugin-export

.pre-commit:
	poetry run pre-commit install
	poetry run pre-commit autoupdate

## инициализирует виртуальное окружение и устанавливает зависимости
setup: clean .install-depends .pre-commit

# BUILD ######################################################

setup_lint: .install-poetry
	poetry install --sync --no-root --only lint

setup_build: .install-poetry
	poetry install --sync --no-root --only build

## Delete .venv and all compiled python files
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf ".mypy_cache"
	rm -rf ".pytest_cache"
	rm -rf $(VENV)
	rm -rf ".ruff_cache"

# DEPLOY ######################################################

.main_reqs:
	poetry export -f requirements.txt \
		--output requirements.txt \
		--only main,build

## Создает или обновляет делоймент в Prefect
deploy: .main_reqs
	yes N | poetry run prefect deploy --all

# POETRY #######################################################

## открывает терминал c виртуальным окружением этого проекта
poetry-shell:
	poetry shell

## обновляет библиотеки
poetry-update:
	poetry update

## проверяет соответсвие .lock и .toml файлов
poetry-check:
	poetry lock --no-update
	poetry check --lock
	poetry lock

# LINT #######################################################

## запускает проверку линтером
lint-check:
	poetry run ruff check $(PROJECT)

sort-imports:
	poetry run ruff check $(PROJECT) --select I --fix
	poetry run ruff format $(PROJECT)

## форматирует код и приводит к pep
lint: sort-imports
	poetry run ruff check $(PROJECT) --fix
	poetry run ruff format $(PROJECT)


# TESTS ########################################################

## запускает тесты
testing:
	poetry run python -m unittest discover -s $(TEST_DIR) -v

## Run tests with pytest tool
pytest:
	poetry run pytest $(TESTMON) $(TEST_DIR) -W ignore::DeprecationWarning

## Run pytest with testmon util (helpful for pre-commit config)
pytest-testmon:
	$(MAKE) pytest TESTMON=--testmon

# SUBMIT #######################################################

## пушит изменения в удаленный репозиторий. Использует версию библиотеки как сообщение коммита
submit:
	git add .
	git commit -m "$(shell poetry version | grep -Eo '[0-9]+\.[0-9]+\.[0-9]+')"
	git push

#################################################################################
# Self Documenting Commands                                                     #
#################################################################################

.DEFAULT_GOAL := help

# Inspired by <http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html>
# sed script explained:
# /^##/:
# 	* save line in hold space
# 	* purge line
# 	* Loop:
# 		* append newline + line to hold space
# 		* go to next line
# 		* if line starts with doc comment, strip comment character off and loop
# 	* remove target prerequisites
# 	* append hold space (+ newline) to line
# 	* replace newline plus comments by `---`
# 	* print line
# Separate expressions are necessary because labels cannot be delimited by
# semicolon; see <http://stackoverflow.com/a/11799865/1968>
.PHONY: help
help:
	@echo "$$(tput bold)Available rules:$$(tput sgr0)"
	@echo
	@sed -n -e "/^## / { \
		h; \
		s/.*//; \
		:doc" \
		-e "H; \
		n; \
		s/^## //; \
		t doc" \
		-e "s/:.*//; \
		G; \
		s/\\n## /---/; \
		s/\\n/ /g; \
		p; \
	}" ${MAKEFILE_LIST} \
	| LC_ALL='C' sort --ignore-case \
	| awk -F '---' \
		-v ncol=$$(tput cols) \
		-v indent=19 \
		-v col_on="$$(tput setaf 6)" \
		-v col_off="$$(tput sgr0)" \
	'{ \
		printf "%s%*s%s ", col_on, -indent, $$1, col_off; \
		n = split($$2, words, " "); \
		line_length = ncol - indent; \
		for (i = 1; i <= n; i++) { \
			line_length -= length(words[i]) + 1; \
			if (line_length <= 0) { \
				line_length = ncol - indent - length(words[i]) - 1; \
				printf "\n%*s ", -indent, " "; \
			} \
			printf "%s ", words[i]; \
		} \
		printf "\n"; \
	}' \
	| more $(shell test $(shell uname) = Darwin && echo '--no-init --raw-control-chars')
