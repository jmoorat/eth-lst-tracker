FROM python:3.11

WORKDIR /usr/src/app

COPY ./requirements.txt .

RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY ./src ./src

CMD ["fastapi", "run", "src/main.py", "--port", "80"]
