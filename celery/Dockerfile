FROM debian:stretch

MAINTAINER François Van Der Biest "francois.vanderbiest@camptocamp.com"

ENV C_FORCE_ROOT true
ENV FONCIER_EXTRACTS_DIR "/extracts"
ENV FONCIER_STATIC_DIR "/static"

RUN apt-get update && apt-get install -y gdal-bin python3 python3-pip python3-psycopg2

# install requirements
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt && rm /tmp/requirements.txt

# copy source code
COPY . /celery
WORKDIR /celery

VOLUME ["/static", "/extracts"]

# run the worker
ENTRYPOINT ["celery", "-A", "extractions", "worker", "--loglevel=info"]