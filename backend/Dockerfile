FROM python:3.12-slim

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*l

WORKDIR /app

RUN pip install poetry

COPY pyproject.toml poetry.lock* ./

RUN poetry install --no-interaction --no-ansi --no-root

COPY . .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

CMD ["poetry", "run", "gunicorn", "--workers=4", "--bind=0.0.0.0:8000", "--access-logfile", "-", "--error-logfile", "-", "my_app.wsgi:application"]
