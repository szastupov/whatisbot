FROM python:3.5

ADD requirements.txt /bot/
ADD main.py /bot/
ADD config.json /bot/
WORKDIR /bot

RUN pip install -r ./requirements.txt

ENV REDIS_HOST redis

CMD ["python", "./main.py"]
