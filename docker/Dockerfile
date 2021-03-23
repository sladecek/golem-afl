FROM golemfactory/base:1.5 
WORKDIR /golem/work
RUN  apt-get update && apt-get install -y libpython3.6
COPY bin/afl-fuzz /
COPY bin/afl-plusplus-fuzz /
VOLUME /golem/input /golem/output /golem/entrypoint /golem/work
