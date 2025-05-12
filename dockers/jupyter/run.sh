#!/bin/bash

# Determine the directory where run.sh script resides
SCRIPT_DIR="$(dirname "$(realpath "$0")")"

# Determine the absolute path to the repo directory
CUSTOM_REPO_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Point the docker to the repo's root directory
docker run -it --rm -p 8889:8888 --name jupyter -v $CUSTOM_REPO_DIR:/home/jovyan/work -d my-custom-jupyter start-notebook.py --NotebookApp.token='docker'
