#!/bin/bash
# get-docker.sh (Jupyter version)

# --- Configuration ---
repo_file="Dockerfile"
line1="FROM quay.io/jupyter/minimal-notebook"
line2=""
line3="RUN pip install --no-cache-dir 'olca-ipc' && \\"
line4='  fix-permissions "${CONDA_DIR}" && \'
line5='  fix-permissions "/home/${NB_USER}"'
line6=""
line7="USER root"
line8=""
line9="RUN apt-get update && apt-get install -y lmodern"

# --- Script Logic ---
if [ -f "$repo_file" ]; then
  echo "Deleting existing file: $repo_file"
  rm "$repo_file"
fi

echo "Creating Dockerfile..."
echo "$line1" >> "$repo_file"
echo "$line2" >> "$repo_file"
echo "$line3" >> "$repo_file"
echo "$line4" >> "$repo_file"
echo "$line5" >> "$repo_file"
echo "$line6" >> "$repo_file"
echo "$line7" >> "$repo_file"
echo "$line8" >> "$repo_file"
echo "$line9" >> "$repo_file"
echo "Done."
exit 0