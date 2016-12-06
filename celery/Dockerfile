FROM python:3.4

MAINTAINER François Van Der Biest "francois.vanderbiest@camptocamp.com"

ENV C_FORCE_ROOT true
ENV FONCIER_EXTRACTS_DIR "/extracts"
ENV FONCIER_STATIC_DIR "/static"

# copy source code
COPY . /celery
WORKDIR /celery

# install requirements
RUN pip install -r requirements.txt

VOLUME ["/static", "/extracts"]

# run the worker
ENTRYPOINT ["celery", "-A", "extractions", "worker", "--loglevel=info"]