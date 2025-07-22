FROM python:alpine3.18

WORKDIR /app

COPY app/* /app

RUN apk upgrade
RUN apk update
RUN apk add musl-dev mariadb-dev gcc
RUN pip install -r requirements.txt
CMD [ "python3", "app.py" ]
