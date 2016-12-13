FROM python:3.4

MAINTAINER François Van Der Biest "francois.vanderbiest@camptocamp.com"

ENV FONCIER_SETTINGS /config.py

WORKDIR "/app"

RUN apt-get update && \
    apt-get install -y \
        python3-all-dev \
        libldap2-dev \
        libsasl2-dev \
    && \
    rm -rf /var/lib/apt/lists/*

COPY resources /

RUN pip install -r /requirements.txt
RUN pip install uwsgi 

COPY foncier /app

EXPOSE 5000

RUN chmod +x /docker-entrypoint.sh /docker-entrypoint.d/*

RUN mkdir /extracts && \
    groupadd --gid 999 www && \
    useradd -r -ms /bin/bash --uid 999 --gid 999 www && \
    chown www:www /extracts

VOLUME ["/extracts"]

USER www

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["uwsgi", "--http", "0.0.0.0:5000", "--callable", "app", "--module", "app", "--chdir", "/app", "--uid", "www"]
