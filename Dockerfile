FROM alpine:3.4

COPY requirements.txt /app/requirements.txt

RUN apk add --update \
    git \
    g++ \
    python \
    python-dev \
    py-pip \
    py-dbus \
  && pip install -r /app/requirements.txt \
  && apk del \
     git \
     g++ \
     python-dev \
  && rm -rf /var/cache/apk/*

COPY src/ /app
WORKDIR /app

ENTRYPOINT ["/usr/bin/python", "-m", "spacel.main"]

