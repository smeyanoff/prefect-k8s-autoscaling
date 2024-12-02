# We're using the latest version of Prefect with Python 3.10
FROM python:3.10.14 AS venv

COPY requirements.txt /requirements.txt

RUN python -m venv venv
RUN /bin/bash -c "source /venv/bin/activate && pip install -r requirements.txt --no-cache-dir"

################################

FROM python:3.10.14 AS app

COPY ./src /opt/prefect/src

COPY --from=venv /venv /venv

ENV VIRTUAL_ENV=/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

CMD ["bash", "-c", "source /venv/bin/activate && prefect worker start --pool test --type kubernetes"]
