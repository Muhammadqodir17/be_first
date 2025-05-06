FROM python:3.13-slim as base

ENV PYTHONUNBUFFERED=1

# Install apt packages
RUN apt-get update && apt-get install --no-install-recommends -y \
  build-essential \
  make \
  curl \
  cron \
  procps \
  git \
  netcat-openbsd \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

RUN pip install --no-cache -U pip setuptools

WORKDIR /opt/app/


COPY requirements.txt /opt/requirements.txt

RUN pip install -r /opt/requirements.txt

COPY entrypoint.sh /opt/entrypoint.sh
RUN chmod +x /opt/entrypoint.sh
ENTRYPOINT ["/opt/entrypoint.sh"]


FROM base as live

COPY . /opt/app/
