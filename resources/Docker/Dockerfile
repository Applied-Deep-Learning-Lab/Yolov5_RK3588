FROM ubuntu:20.04
ARG DEBIAN_FRONTEND=noninteractive
ENV PATH="/root/miniconda3/bin:${PATH}"
ARG PATH="/root/miniconda3/bin:${PATH}"

# Install dependencies
RUN apt-get update && \
    apt-get -y upgrade && \
    apt-get install -y git wget cmake g++ gcc tar libx11-dev xorg-dev libssl-dev build-essential libusb-1.0.0-dev && \
    apt-get install -y python3 python3-dev python3-pip

# Install and configure python3.9
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh && \
    mkdir /root/.conda && \
    bash Miniconda3-latest-Linux-aarch64.sh -b && \
    rm -f Miniconda3-latest-Linux-aarch64.sh && \
    conda init bash && \
    . /root/.bashrc && \
    conda update conda && \
    conda create -n rknn python=3.9 && \
    conda activate rknn && \
    echo "conda activate rknn" >> ~/.bashrc

# Install project and install python whl
RUN mkdir workspace/ && cd workspace/ && \
    git clone https://github.com/Applied-Deep-Learning-Lab/Yolov5_RK3588 && \
    cd Yolov5_RK3588/RK3588/rknpu2_python3/install && \
    pip install rknn_toolkit_lite2-1.4.0-cp39-cp39-linux_aarch64.whl && \
    pip install opencv-python