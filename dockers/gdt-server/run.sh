#!/bin/bash
# Set the path to the directory to read from
folder_path=~/openLCA-data-1.4/databases

# List all folders in the directory
# SOURCE: https://superuser.com/a/760900
echo "Available databases:"

# Read user input for openLCA database to open
for f in $folder_path/* ; do echo $(basename $f) ; done

echo "Enter openLCA database name to open: "
read folder_name

# This creates GDT service on localhost:3000
docker run --rm --name gdt-server -p 3000:8000 -v ~/openLCA-data-1.4:/app/data -d gdt-server -db $folder_name --readonly
