FROM alpine:3.11 AS builder

ADD requirements.txt /requirements.txt

RUN apk add python3 python3-dev gcc musl-dev libffi-dev openssl-dev libxml2-dev xmlsec-dev build-base

ENV MAKEFLAGS='-j6'

RUN pip3 install -r /requirements.txt

RUN mkdir /code
ADD code/ /code

ENTRYPOINT ["python3","/code/main.py"]
