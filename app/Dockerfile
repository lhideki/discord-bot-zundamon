FROM python:3.11-slim

WORKDIR /workspace
RUN pip install poetry
COPY poetry.lock pyproject.toml README.md ./
RUN poetry config virtualenvs.create false
COPY app/serve.py ./

RUN poetry install --only main

CMD [ "python3" , "serve.py" ]