from ubuntu:latest

RUN apt-get update \
    && apt-get install -y python3-dev \
    && apt-get install -y python3-pip

WORKDIR /ConfusionMatrixAPI

COPY . /ConfusionMatrixAPI

RUN pip3 --no-cache-dir install -r requirements.txt

ENTRYPOINT  ["python3"]

CMD ["app.py"]