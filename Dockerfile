FROM alpine:3.11 AS builder

ADD requirements.txt /requirements.txt

RUN apk add python3 python3-dev gcc musl-dev libffi-dev openssl-dev build-base

RUN pip3 install -r /requirements.txt


FROM alpine:3.11

ENV TELEGRAM_BOT_TOKEN=""
ENV TELEGRAM_USER_ID=""
ENV IB_TOKEN=""

RUN mkdir /code
ADD code/ /code

RUN apk add python3

COPY --from=builder /lib/python/site-packages/ /lib/pyton/site-packages/

ENTRYPOINT ["python","/code/code/main.py"]
