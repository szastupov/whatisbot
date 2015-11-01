FROM python:3.5

ADD main.py /bot/
ADD config.json /bot/
WORKDIR /bot

RUN pip install git+git://github.com/szastupov/aiotg.git@master
RUN pip install aioredis

ENV REDIS_HOST redis

CMD ["python", "./main.py"]
