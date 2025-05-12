#!/bin/bash
# get-docker.sh (GDT server version)

# --- Configuration ---
repo_url="https://github.com/GreenDelta/gdt-server"
repo_dir="gdt-server"
repo_file="Dockerfile"

# --- Script Logic ---

# 1. Clone the repository; only pull the latest commit for speed
echo "Cloning repository..."
git clone --depth 1 "$repo_url"

if [ $? -ne 0 ]; then
  echo "Error cloning repository. Exiting."
  exit 1
fi

# 2. Copy the desired file
echo "Copying file..."
cp "$repo_dir/$repo_file" "$repo_file"

if [ $? -ne 0 ]; then
  echo "Error copying file. Exiting."
  # Clean up the repository
  rm -rf "$repo_dir"
  exit 1
fi

echo "File copied successfully to: $repo_file"

# 3. Delete the cloned repository
echo "Deleting temporary repository..."
rm -rf "$repo_dir"

if [ $? -ne 0 ]; then
  echo "Error deleting temporary repository."
fi

echo "Done."
exit 0