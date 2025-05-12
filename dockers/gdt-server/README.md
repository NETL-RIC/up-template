# Docker Instructions
These instructions assume that openLCA v2 (or greater) is installed and that at least one database is created.

## Linux and macOS

From a BASH terminal, run the following:

1. Make sure docker is installed and running.

   `docker --version`

2. Get the Dockerfile

   `bash get-docker.sh`

3. Build the image

   `bash build.sh`

4. Run the container

   `bash run.sh`

   Follow the prompt to select the openLCA database to open.

## Windows 10

From the command prompt, run the following:

1. Make sure docker is installed and running.

   `docker --version`

2. Get the Dockerfile

   `cmd /c get-docker.bat`

3. Build the image

   `cmd /c build.bat`

4. Run the container

   `cmd /c run.bat`

   Follow the prompt to select the openLCA database to open.
