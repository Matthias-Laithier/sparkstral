FROM python:3.13-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml ./
RUN uv sync --no-dev

COPY src ./src

CMD ["uv", "run", "--no-dev", "python", "-m", "src.worker"]
