FROM alpine:3.11 AS builder

ADD requirements.txt .

RUN apk add python3 python3-dev gcc musl-dev libffi-dev openssl-dev libxml2-dev xmlsec-dev build-base

RUN pip3 install --user -r requirements.txt


FROM alpine:3.11

RUN apk add python3 libstdc++ py3-lxml

COPY --from=builder /root/.local /root/.local

RUN mkdir /code
ADD code/ /code

RUN mkdir -p /root/.local
ENV PATH=/root/.local/bin:$PATH

ENTRYPOINT ["python3","/code/main.py"]
