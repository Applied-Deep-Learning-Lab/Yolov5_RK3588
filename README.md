<h1>
    Yolov5_RK3588
</h1>

<details open>
  <summary>
    <h2>
      <p>
        1. Prerequisites
        <img src="https://www.svgrepo.com/show/288488/motherboard.svg" width=38 height=38 alt="Prerequisites" />
      </p>
    </h2>
  </summary>   
  
  * ### Ubuntu

    Install Ubuntu on your RK3588 device. *(tested on Ubuntu 20.04 and OrangePi5/Firefly ROC RK3588S devices)*

    For installing Ubuntu on Firefly you can use their manual[[1]](https://wiki.t-firefly.com/en/ROC-RK3588S-PC/index.html)[[2]](https://en.t-firefly.com/doc/download/page/id/142.html).

    For installing Ubuntu on OrangePi you can use [their manual](http://www.orangepi.org/html/hardWare/computerAndMicrocontrollers/service-and-support/Orange-pi-5.htmlfi).

    Or use ours **README's** for them *(select the one below)*.

    |[OrangePi](resources/OrangePi/README_ORANGEPI.md)|[Firefly](resources/Firefly/README_FIREFLY.md)|
    |                 :---:                 |                :---:               |

  * ### Docker *(Optional)*

    For installing docker on RK3588 device you can use [official docker docs](https://docs.docker.com/desktop/install/linux-install/) or check our [README_DOCKER.md](README_DOCKER.md)

</details>  

<details open>
  <summary>
    <h2>
      <p>
        2. Install docker images <i>(Optional)</i>
        <img src="https://opennebula.io/wp-content/uploads/2020/05/DockerHub.png" height=38 alt="Docker Hub" />
      </p>
    </h2>
  </summary>

  * ### From Docker hub <a href="https://hub.docker.com/r/deathk9t/yolov5_rk3588"><img src="https://img.shields.io/badge/yolov5_rk3588--blue?logo=docker"></a>

    At first you need download docker image:

    ```
    docker pull deathk9t/yolov5_rk3588:latest
    ```

    Then you can run container with:

    ```
    docker run --privileged --name [container-name] -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix -v /dev/:/dev --network host -it deathk9t/yolov5_rk3588:latest
    ```

  * ### Build docker image by yourself

    You can build docker image by yourself usning **Dockerfile**:
    
    ```
    docker build -t [name-docker-image:tag] .
    ```

    Then you can run container with:

    ```
    docker run --privileged --name [container-name] -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix -v /dev/:/dev --network host -it [name-docker-image:tag]
    ```

</details>

<details open>
  <summary>
    <h2>
      <p>
        3. Installing, Configurating and Running Yolov5
        <img src="https://storage.googleapis.com/wandb-production.appspot.com/wandb-public-images/3hql0qh3b7.png" width=38 height=38 alt="Yolov5" />
      </p>
    </h2>
  </summary>

  Install miniconda

  ```
  wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh
  bash Miniconda3-latest-Linux-aarch64.sh
  ```

  Create conda env with python3.9

  ```
  conda create -n <env-name> python=3.9
  ```
  
  And then activate conda env

  ```
  conda activate <env-name>
  ```

  Install RKNN-Toolkit2-Lite???such as rknn_toolkit_lite2-1.4.0-cp39-cp39-linux_aarch64.whl

  ```
  #cd <repo-dir>/install/
  pip install rknn_toolkit_lite2-1.4.0-cp39-cp39-linux_aarch64.whl
  ```

  Run inference
  
  ```
  python3 main.py
  ```

</details>

<details open>
  <summary>
    <h2>
      <p>
        4. Convert onnx model to rknn 
        <img src="https://external-content.duckduckgo.com/iu/?u=http%3A%2F%2Fds2converter.com%2Fwp-content%2Fuploads%2F2015%2F07%2Fconvert-icon.png&f=1&nofb=1&ipt=d6dbe833ced7274d7335d067ba819d63567e853dc093822f5cda0d18df3bfbdf&ipo=images" width=38 height=38 alt="Converter" />
      </p>
    </h2>
  </summary>

  * ### Host PC

      Install Python3 and pip3

      ```
      sudo apt-get install python3 python3-dev python3-pip
      ```

      Install dependent libraries

      ```
      sudo apt-get install libxslt1-dev zlib1g zlib1g-dev libglib2.0-0 libsm6 libgl1-mesa-glx libprotobuf-dev gcc git
      ```

      Install Python dependency, such as requirements_cp38-1.4.0.txt

      ```
      #cd <repo_dir>/resources/HostPC/converter/install/
      pip install -r requirements_cp38-1.4.0.txt
      #if doesn't installing then install numpy before that
      #pip install numpy
      ```
      
      Install RKNN-Toolkit2???such as rknn_toolkit2-1.4.0_22dcfef4-cp38-cp38-linux_x86_64.whl

      ```
      pip install rknn_toolkit2-1.4.0_22dcfef4-cp38-cp38-linux_x86_64.whl
      ```

      For convert your *.onnx* model to *.rknn* run **onnx2rknn.py** like:

      ```
      #cd <repo-dir>/resources/HostPC/converter/convert/
      python3 onnx2rknn.py \
              --input <path-to-your-onnx-model> \
              --output <path-where-save-rknn-model> \
              --dataset <path-to-txt-file-with-calibration-images-names>
      ```

</details>