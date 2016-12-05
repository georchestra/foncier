FROM python:2.7

MAINTAINER François Van Der Biest "francois.vanderbiest@camptocamp.com"

ENV CELERY_BROKER_URL redis://redis:6379/0
ENV CELERY_RESULT_BACKEND redis://redis:6379/0
ENV C_FORCE_ROOT true

# copy source code
COPY . /celery
WORKDIR /celery

# install requirements
RUN pip install -r requirements.txt

# run the worker
#ENTRYPOINT ['celery']
#CMD ['-A','tasks', 'worker','--loglevel=info']
ENTRYPOINT celery -A extractions worker --loglevel=info