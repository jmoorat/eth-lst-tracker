FROM python:3.11-bullseye

WORKDIR /usr/src/app

ARG LOG_LEVEL=INFO

ENV LOG_LEVEL=$LOG_LEVEL

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY config.json .

CMD ["python", "src/lsdtracker.py", "-c", "config.json"]
