# Setting up sMRIprep Docker

The sMRIprep pipeline is provided as a [Docker image](https://hub.docker.com/r/nipreps/smriprep/tags/). In order to run the pipeline, [Docker](https://www.docker.com/products/docker-desktop/) needs to be installed. In some cases, primarily due to security reasons, the [rootless version of Docker](https://docs.docker.com/engine/security/rootless/) needs to be installed. In that case, it might be necessary to change the proxy settings of the default configuration of Docker so that it can connect to the internet, which is required for pulling images from Docker Hub.

Once Docker is running, the image of the pipeline needs to be downloaded with the command.

```bash
   docker pull nipreps/smriprep:latest 
```