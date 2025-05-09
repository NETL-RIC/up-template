@echo off
setlocal enabledelayedexpansion

rem Set the path to the directory to read from
set folder_path=%USERPROFILE%\openLCA-data-1.4\databases

rem List all folders in the directory
for /f "tokens=*" %%f in ('dir /b /ad "%folder_path%"') do (
    echo %%f
)

rem Read user input to select a folder
set /p folder_name="Enter openLCA database name to open: "

docker run --name gdt-server ^
  -p 3000:8080 ^
  -v %USERPROFILE%/openLCA-data-1.4:/app/data ^
  --rm ^
  -d gdt-server ^
  -db !folder_name! ^
  --readonly
