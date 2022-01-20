FROM ubuntu:latest

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    vim \
    tmux \
    wget \
    curl

RUN mkdir /AkitaAlgorandNodeInterface

ADD . /AkitaAlgorandNodeInterface/

CMD pip install -r /AkitaAlgorandNodeInterface/requirements.txt && \
    cd /AkitaAlgorandNodeInterface/ && \
    python3 /AkitaAlgorandNodeInterface/main.py && \
    tail -f /dev/null