FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir "poetry==2.3.2"

# Copy dependency files first (cache-friendly)
COPY pyproject.toml poetry.lock ./

# Install dependencies only (do not install the project yet)
RUN poetry config virtualenvs.create false \
 && poetry install --no-interaction --no-ansi --no-root

# Now copy application code
COPY src ./src
COPY alembic ./alembic
COPY alembic.ini ./

# Install the project itself (fast, without reinstalling deps)
RUN poetry install --no-interaction --no-ansi --only-root

EXPOSE 8000

CMD ["poetry", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
