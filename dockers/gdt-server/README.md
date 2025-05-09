# Docker Instructions
These instructions assume that openLCA v2 (or greater) is installed and that at least one database is created.

## Linux and macOS

From a BASH terminal, run the following:

1. Make sure docker is installed and running.

   `docker --version`

2. Get the Dockerfile

   `bash get-docker.sh`

3. Build the image (copy build.bat to gdt-server directory)

   `bash build.sh`

4. Run the container (copy the run.bat to gdt-server directory)

   `bash run.sh`

   Follow the prompt to select the openLCA database to open.

## Windows 10

From the command prompt, run the following:

1. Make sure docker is installed and running.

   `docker --version`

2. Get the Dockerfile

   `git clone https://github.com/GreenDelta/gdt-server.git`

3. Build the image (copy build.bat to gdt-server directory)

   `cmd /c build.bat`

4. Run the container (copy the run.bat to gdt-server directory)

   `cmd /c run.bat`

   Follow the prompt to select the openLCA database to open.
