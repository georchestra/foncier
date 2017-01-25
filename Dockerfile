FROM debian:stretch

MAINTAINER François Van Der Biest "francois.vanderbiest@camptocamp.com"

WORKDIR "/app"

RUN apt-get update && \
    apt-get install -y \
        python3-all-dev \
        libldap2-dev \
        libsasl2-dev \
        uwsgi \
        python3-pip \
    && \
    rm -rf /var/lib/apt/lists/*

RUN apt-get update && \
    apt-get install -y uwsgi uwsgi-plugin-python3 \
    && \
    rm -rf /var/lib/apt/lists/*

COPY resources /

RUN pip3 install -r /requirements.txt

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
CMD ["uwsgi", "--plugin", "python3,http,router_static", "--http-socket", "0.0.0.0:5000", "--callable", "app", "--module", "app", "--chdir", "/app", "--uid", "www"]
