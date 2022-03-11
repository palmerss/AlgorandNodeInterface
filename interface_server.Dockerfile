FROM ubuntu:latest

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    vim \
    tmux \
    wget \
    curl

RUN mkdir /AlgorandNodeInterface

ADD . /AlgorandNodeInterface/

CMD pip install -r /AlgorandNodeInterface/requirements.txt && \
    cd /AlgorandNodeInterface/ && \
    python3 /AlgorandNodeInterface/main.py && \
    tail -f /dev/null