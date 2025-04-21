FROM python:3.13

ARG LOG_LEVEL=INFO

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates
ADD https://astral.sh/uv/0.6.14/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin/:$PATH"

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY src ./src
COPY config.json .

ENV LOG_LEVEL=$LOG_LEVEL

CMD ["uv", "run", "src/main.py", "-c", "config.json"]
