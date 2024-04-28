FROM ubuntu:latest

ARG LOG_LEVEL=INFO

ENV DATABASE_URL="" \
    LOG_LEVEL=$LOG_LEVEL \
    WEB3_PROVIDER="" \
    HTTP_PROXY="" \
    ONE_INCH_API_KEY=""

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-setuptools \
    python3-venv \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --upgrade pip
RUN mkdir /app
WORKDIR /app
COPY requirements.txt /app
RUN pip3 install -r requirements.txt
COPY src /app/src
COPY config.json /app

CMD ["python3", "src/lsdtracker.py", "-c", "config.json"]
