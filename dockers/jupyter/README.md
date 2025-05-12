# Docker Instructions
The Dockerfile is based on the [minimal-notebook](https://jupyter-docker-stacks.readthedocs.io/en/latest/using/selecting.html#jupyter-minimal-notebook) image.
Portions of the get-docker and run shell and batch scripts were written by AI.

## Linux or macOS

1. Make sure docker is installed and running.

   `docker --version`

2. Create the Dockerfile.

   `bash get-docker.sh`

3. Build the image

   `bash build.sh`

4. Run the container.

      `bash run.sh`

## Windows 10

1. Make sure docker is installed and running.

   `docker --version`

2. Create the Dockerfile.

   `cmd /c get-docker.bat`

2. Build the image.

      `cmd /c build.bat`

4. Run the container.

      `cmd /c run.bat`
