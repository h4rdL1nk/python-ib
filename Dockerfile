FROM alpine:3.11 AS builder

ADD requirements.txt /requirements.txt

RUN apk add python3 python3-dev --virtual build-pkgs gcc musl-dev libffi-dev openssl-dev libxml2-dev xmlsec-dev build-base \
    && pip3 install -r /requirements.txt \
    && apk del build-pkgs

#RUN apk add python3 python3-dev libffi-dev openssl-dev build-base py3-prettytable py3-requests py3-lxml py3-numpy py3-cryptography

RUN mkdir /code
ADD code/ /code

ENTRYPOINT ["python3","/code/main.py"]
