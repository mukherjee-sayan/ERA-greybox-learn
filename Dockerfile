# syntax=docker/dockerfile:1

FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    python3 \
    python3-pip

WORKDIR /ERA-greybox-learn

RUN mkdir -p tools

# install dependencies for TChecker
ARG LIBBOOST_VERSION=1.81
ENV LIBBOOST_VERSION=${LIBBOOST_VERSION}

ARG CATCH2_REV=v3.4.0
ARG CATCH2_REPO=https://github.com/catchorg/Catch2.git

RUN apt-get update && \
    apt-get install -y \
    cmake bison flex doxygen \
    libboost-all-dev  

# install dependencies for TChecker
RUN git clone --branch ${CATCH2_REV} ${CATCH2_REPO} /tools/catch2

RUN mkdir -p /tools/catch2/build && \
    cd /tools/catch2/build && \
    cmake -DCMAKE_CXX_COMPILER=g++ .. && \
    make && \
    make install

# install TChecker
RUN cd tools && mkdir -p tchecker && \
    cd tchecker && \
    git clone https://github.com/ticktac-project/tchecker.git && \
    mkdir build && mkdir install && \
    cd build && \
    cmake ../tchecker -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=../install && \
    make && make doc && make install

# install dependencies for tLsep
RUN pip3 install z3-solver
RUN pip3 install prettytable

COPY tlsep/ /ERA-greybox-learn/tlsep
COPY examples/ /ERA-greybox-learn/examples
