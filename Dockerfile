FROM python:3.12-slim

RUN pip install pdm

ENV PYTHONUNBUFFERED=1 \
    PDM_IGNORE_SAVED_PYTHON=1

WORKDIR /app

COPY . /app

RUN pdm install --prod

CMD ["pdm", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
