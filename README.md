<h1>
    rk3588-neural-networks
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

    For installing Ubuntu on OrangePi you can use [their manual](http://www.orangepi.org/html/hardWare/computerAndMicrocontrollers/service-and-support/Orange-pi-5.html).

    Or use ours **README's** for them *(select the one below)*.

    |[OrangePi](resources/OrangePi/README_ORANGEPI.md)|[Firefly](resources/Firefly/README_FIREFLY.md)|
    |                 :---:                 |                :---:               |

  * ### FFMPEG

    Install ffmpeg package for WebUI:

    ```
    sudo apt-get update
    sudo apt-get install -y ffmpeg
    ```

    And dependencies for WebUI:
    
    ```
    sudo apt-get update
    # General dependencies
    sudo apt-get install -y python-dev pkg-config

    # Library components
    sudo apt-get install libavformat-dev libavcodec-dev libavdevice-dev\
      libavutil-dev libswscale-dev libswresample-dev libavfilter-dev
    ```

    Open .bashrc  in nano text editor:

    ```
    nano ~/.bashrc
    ```

    At the end of file add next line:

    ```
    export LD_PRELOAD=$LD_PRELOAD:/usr/lib/aarch64-linux-gnu/libffi.so.7
    ```

    Save and close nano with sortcuts ctrl-o, Enter, ctrl-x

</details>  

<details open>
  <summary>
    <h2>
      <p>
        2. Installing and configurating
        <img src="resources/HostPC/images/installing.jpg" width=38 height=38 alt="Neural Networks" />
      </p>
    </h2>
  </summary>

  Install miniconda

  ```
  wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh
  bash Miniconda3-latest-Linux-aarch64.sh
  ```

  Then rerun terminal session:

  ```
  source ~/.bashrc
  ```

  Create conda env with python3.9

  ```
  conda create -n <env-name> python=3.9
  ```
  
  And then activate conda env

  ```
  conda activate <env-name>
  ```

  Clone repository:

  ```
  git clone https://github.com/Applied-Deep-Learning-Lab/rk3588-neural-networks
  ```

  And got into repo-dir:

  ```
  cd rk3588-neural-networks
  ```

  Install RKNN-Toolkit2-Lite，such as rknn_toolkit_lite2-1.5.0-cp39-cp39-linux_aarch64.whl

  ```
  pip install install/rknn_toolkit_lite2-1.5.0-cp39-cp39-linux_aarch64.whl
  ```

  In created conda enviroment also install requirements from the same directory

  ```
  pip install -r install/requirements.txt
  ```

  Then go to the install dir for building and installing cython_bbox

  ```
  cd install/cython_bbox
  python3 setup.py build
  python3 setup.py install
  ```

</details>

<details open>
  <summary>
    <h2>
      <p>
        3. Running
        <img src="resources/HostPC/images/running.png" width=38 height=38 alt="Neural Networks" />
      </p>
    </h2>
  </summary>

  Before running, you can configure all options for the neural network(s) and enable/disable some options (modules) for the main program.

  In ``main.py`` file you can choose which neural network(s) you want to run. Simply type in single (or multiple) words from the following choices: **PIDNET_CFG, YOLACT_CFG, YOLOV5_CFG**

  Weights for neural networks you could take from: [[our another repo]](https://github.com/Applied-Deep-Learning-Lab/Yolov5_RK3588/tree/main/models) \[earlier commits of this repo\] [[rknn-toolkit2]](https://github.com/rockchip-linux/rknn-toolkit2/tree/master/examples) [[rknpu2]](https://github.com/rockchip-linux/rknpu2/tree/master/examples).

  After configurating run inference.
  
  ```
  python3 main.py
  ```

  For see WebUI *(if it was enabled)* write to browser address bar next *(localhost - device's ip)*:

  ```
  # aiortc
  localhost:8080

  # flask
  localhost:5000
  ```

  You also can set autostart for running this.

  Before it deactivate conda env:

  ```
  conda deactivate
  ```

  * For Orange Pi

    ```
    source install/autostart/orangepi_autostart.sh
    ```

  * For Firefly:

    ```
    source install/autostart/firefly_autostart.sh
    ```

</details>

<details>
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
      sudo apt-get update
      sudo apt-get install python3 python3-dev python3-pip
      ```

      Install dependent libraries

      ```
      sudo apt-get update
      sudo apt-get install libxslt1-dev zlib1g zlib1g-dev libglib2.0-0 libsm6 libgl1-mesa-glx libprotobuf-dev gcc git
      ```
      
      Install RKNN-Toolkit2，such as rknn_toolkit2-1.4.0_22dcfef4-cp38-cp38-linux_x86_64.whl

      ```
      pip install resources/HostPC/converter/install/rknn_toolkit2-1.4.0_22dcfef4-cp38-cp38-linux_x86_64.whl
      ```

      For convert your *.onnx* model to *.rknn* run **onnx2rknn.py** like:

      ```
      cd resources/HostPC/converter/convert/
      python3 onnx2rknn.py \
              --input <path-to-your-onnx-model> \
              --output <path-where-save-rknn-model> \
              --dataset <path-to-txt-file-with-calibration-images-names>
      ```

</details>
