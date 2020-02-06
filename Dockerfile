FROM alpine:3.11 AS builder

ADD requirements.txt /requirements.txt

#RUN apk add python3 python3-dev gcc musl-dev libffi-dev openssl-dev libxml2-dev xmlsec-dev build-base
RUN apk add python3 python3-dev libffi-dev openssl-dev build-base py3-prettytable py3-requests py3-lxml py3-numpy py3-cryptography

RUN pip3 install -r /requirements.txt

RUN mkdir /code
ADD code/ /code

ENTRYPOINT ["python3","/code/main.py"]
