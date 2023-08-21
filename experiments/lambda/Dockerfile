FROM public.ecr.aws/lambda/python:3.11

RUN pip install poetry
COPY poetry.lock pyproject.toml README.md ./
RUN poetry config virtualenvs.create false
COPY app/huggingface ./
COPY app/discord-chatbot.py ./

RUN poetry install --only main

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "discord-chatbot.lambda_handler" ]