FROM debian:stretch

MAINTAINER François Van Der Biest "francois.vanderbiest@camptocamp.com"

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
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

RUN mkdir /extracts /static && \
    groupadd --gid 999 www && \
    useradd -r -ms /bin/bash --uid 999 --gid 999 www && \
    chown www:www /extracts /static

VOLUME ["/static", "/extracts"]

USER www

# run the worker
ENTRYPOINT ["celery", "-A", "extractions", "worker", "--loglevel=info", "--concurrency=1"]
