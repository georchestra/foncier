FROM python:2.7

MAINTAINER François Van Der Biest "francois.vanderbiest@camptocamp.com"

ENV C_FORCE_ROOT true

# copy source code
COPY . /celery
WORKDIR /celery

# install requirements
RUN pip install -r requirements.txt

# run the worker
ENTRYPOINT ['celery', '-A', 'extractions', 'worker', '--loglevel=info']