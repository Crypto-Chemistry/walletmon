FROM python:3.10-alpine AS base
RUN apk update && apk upgrade && \
    apk add --no-cache git
RUN git clone https://github.com/Crypto-Chemistry/walletmon.git /walletmon
WORKDIR /walletmon
RUN pip3 install -r requirements.txt

ENTRYPOINT [ "python3" ]
