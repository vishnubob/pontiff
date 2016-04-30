FROM ubuntu:14.04
MAINTAINER Giles Hall

RUN apt-get update && \
    apt-get -y install python python-dev python-pip \
    python-numpy python-scipy libfreetype6-dev libffi-dev libmemcached-dev libcairo2-dev ssh
RUN pip install pillow deap cairosvg pylru freetype-py pylibmc simanneal svgwrite
RUN mkdir /tmp/src
COPY / /tmp/src
WORKDIR /tmp/src

CMD ["python", "runner.py"]
