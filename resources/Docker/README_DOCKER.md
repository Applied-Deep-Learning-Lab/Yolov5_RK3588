<h1>
    <p> 
    Installing and Configuring Docker
    <a href="https://www.docker.com/">
        <img src="https://upload.wikimedia.org/wikipedia/commons/4/4e/Docker_%28container_engine%29_logo.svg" width=160 height=38 alt="Docker" />
    </a>
    </p>
</h1> 
  
  * ## Installing

    First, update your existing list of packages:

    ```
    sudo apt update
    ```

    Next, install a few prerequisite packages which let ``apt`` use packages over HTTPS:

    ```
    sudo apt install apt-transport-https ca-certificates curl software-properties-common
    ```

    Then add the GPG key for the official Docker repository to your system:

    ```
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
    ```

    Add the Docker repository to APT sources:

    ```
    sudo add-apt-repository "deb https://download.docker.com/linux/ubuntu focal stable"
    ```

    This will also update our package database with the Docker packages from the newly added repo.  
    Make sure you are about to install from the Docker repo instead of the default Ubuntu repo:

    ```
    apt-cache policy docker-ce

    #Output
    docker-ce:
      Installed: (none)
      Candidate: 5:19.03.9~3-0~ubuntu-focal
      Version table:
          5:19.03.9~3-0~ubuntu-focal 500
            500 https://download.docker.com/linux/ubuntu focal/stable amd64 Packages
    ```

    Notice that ``docker-ce`` is not installed, but the candidate for installation is from the Docker repository for Ubuntu 20.04 (``focal``).  
    Finally, install Docker:

    ```
    sudo apt install docker-ce
    ```

    Docker should now be installed, the daemon started, and the process enabled to start on boot. Check that it’s running:

    ```
    sudo systemctl status docker

    #Output
    ● docker.service - Docker Application Container Engine
          Loaded: loaded (/lib/systemd/system/docker.service; enabled; vendor preset: enabled)
          Active: active (running) since Tue 2020-05-19 17:00:41 UTC; 17s ago
    TriggeredBy: ● docker.socket
            Docs: https://docs.docker.com
        Main PID: 24321 (dockerd)
          Tasks: 8
          Memory: 46.4M
          CGroup: /system.slice/docker.service
                  └─24321 /usr/bin/dockerd -H fd:// --containerd=/run/containerd/containerd.sock
    ```

  * ## Executing the Docker Command Without Sudo

    By default, the ``docker`` command can only be run the **root** user or by a user in the **docker** group, which is automatically created during Docker’s installation process. If you attempt to run the ``docker`` command without prefixing it with ``sudo`` or without being in the **docker** group, you’ll get an output like this:

    ```
    #Output
    docker: Cannot connect to the Docker daemon. Is the docker daemon running on this host?.  
    See 'docker run --help'.
    ```

    If you want to avoid typing sudo whenever you run the docker command, add your username to the docker group:

    ```    
    sudo usermod -aG docker ${USER}
    ```
      
    To apply the new group membership, log out of the server and back in, or type the following:

    ```
    su - ${USER}
    ```
      
    You will be prompted to enter your user’s password to continue.  
    Confirm that your user is now added to the docker group by typing:

    ```
    groups
    
    #Output
    <some-groups> docker
    ```